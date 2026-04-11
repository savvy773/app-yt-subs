import asyncio
import csv
import json
import random
import flet as ft
from pathlib import Path
from playwright.async_api import async_playwright

# 설정 경로
ROOT_DIR = Path("D:/Code/Python/yt_subs")
USER_DATA_DIR = ROOT_DIR / "user_data"
SUBS_FILE = ROOT_DIR / "subscriptions.csv"
CONFIG_FILE = ROOT_DIR / "config.json"

class YTManagerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "YouTube 구독 관리자 (Background Support) 🚀"
        self.page.theme_mode = ft.ThemeMode.DARK
        
        self.config = {"width": 600, "height": 800, "top": 100, "left": 100}
        self.load_config()
        self.apply_window_settings()
        
        # UI 요소들
        self.log_area = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)
        self.progress_bar = ft.ProgressBar(width=500, color="blue", bgcolor="#222222", value=0, visible=False)
        self.status_text = ft.Text("상태: 대기 중", color="white70")
        
        # 백그라운드 모드 스위치
        self.bg_switch = ft.Switch(label="백그라운드 모드 (브라우저 창 숨기기)", value=False, label_position=ft.LabelPosition.LEFT)
        
        self.page.window.on_event = self.on_window_event
        self.setup_ui()

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    saved = json.load(f)
                    for k in self.config.keys():
                        if k in saved and saved[k] is not None: self.config[k] = saved[k]
            except: pass

    def save_config(self):
        try:
            w, h, t, l = self.page.window.width, self.page.window.height, self.page.window.top, self.page.window.left
            if all(v is not None for v in [w, h, t, l]):
                self.config.update({"width": w, "height": h, "top": t, "left": l})
                with open(CONFIG_FILE, "w") as f: json.dump(self.config, f)
        except: pass

    def apply_window_settings(self):
        self.page.window.width, self.page.window.height = self.config["width"], self.config["height"]
        self.page.window.top, self.page.window.left = self.config["top"], self.config["left"]
        self.page.update()

    async def on_window_event(self, e):
        if e.data in ["moved", "resized"]: self.save_config()

    def setup_ui(self):
        header = ft.Column([
            ft.Text("YouTube Subscriptions", size=32, weight="bold", color="blue"),
            ft.Text("안정 모드 + 백그라운드 처리가 지원됩니다.", color="white70", size=14),
        ])
        
        # 옵션 섹션
        options = ft.Container(
            content=self.bg_switch,
            padding=10,
            bgcolor="#222222",
            border_radius=10,
            alignment=ft.alignment.center
        )

        action_buttons = ft.Row([
            ft.FilledButton("백업 (Export)", icon=ft.Icons.DOWNLOAD, on_click=self.on_export_click, style=ft.ButtonStyle(bgcolor="blue700", color="white")),
            ft.FilledButton("전체 삭제 (Clear)", icon=ft.Icons.DELETE_FOREVER, on_click=self.on_clear_click, style=ft.ButtonStyle(bgcolor="red700", color="white")),
            ft.FilledButton("복원 (Import)", icon=ft.Icons.UPLOAD, on_click=self.on_import_click, style=ft.ButtonStyle(bgcolor="green700", color="white")),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        
        log_container = ft.Container(
            content=self.log_area, bgcolor="#1A1A1A", border_radius=10, padding=10, expand=True, border=ft.Border.all(1, "#333333")
        )
        
        self.page.add(
            header, ft.Divider(height=20, color="transparent"),
            options, ft.Divider(height=10, color="transparent"),
            action_buttons, ft.Divider(height=30, color="#333333"),
            self.status_text, self.progress_bar, ft.Text("실시간 로그", size=12, color="white40"),
            log_container
        )

    def log(self, message, color="white"):
        self.log_area.controls.append(ft.Text(message, color=color, size=13))
        self.page.update()

    async def get_browser_context(self, p):
        if not USER_DATA_DIR.exists(): USER_DATA_DIR.mkdir(parents=True)
        headless = self.bg_switch.value
        if headless:
            self.log("💡 백그라운드 모드: 브라우저 창 없이 실행합니다.", "white60")
        
        return await p.chromium.launch_persistent_context(
            str(USER_DATA_DIR), 
            headless=headless, 
            channel="chrome",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            ignore_default_args=["--enable-automation"],
            args=["--start-maximized", "--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-infobars"]
        )

    async def human_delay(self, min_sec=2.5, max_sec=5.0):
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def ensure_logged_in_and_navigate(self, page, target_url):
        self.log("구글 환경 확인 중...", "white60")
        await page.goto("https://www.google.com")
        await asyncio.sleep(2)
        await page.goto(target_url)
        
        if "accounts.google.com" in page.url or await page.query_selector('a:has-text("로그인")'):
            if self.bg_switch.value:
                self.log("❌ 오류: 로그인이 필요합니다! 백그라운드 모드를 끄고 먼저 로그인해 주세요.", "red")
                raise Exception("Login Required")
            
            self.log("⚠️ 로그인이 필요합니다. 창에서 로그인을 마쳐주세요!", "yellow")
            await page.wait_for_url(lambda url: "youtube.com/feed/channels" in url or "youtube.com/@" in url, timeout=0)
            self.log("✅ 로그인 성공! 작업을 이어갑니다.", "green")
            await self.human_delay(3, 5)
            await page.goto(target_url)
        else:
            self.log("✅ 로그인 상태 확인 완료", "green")

    async def on_export_click(self, e):
        self.log("--- 백업 자동화 시작 ---", "blue")
        self.progress_bar.visible, self.progress_bar.value = True, None
        self.page.update()
        try:
            async with async_playwright() as p:
                context = await self.get_browser_context(p)
                page = await context.new_page()
                await self.ensure_logged_in_and_navigate(page, "https://www.youtube.com/feed/channels")
                
                self.log("채널 스캔 중... (잠시 다른 일을 하셔도 됩니다)")
                last_height = 0
                while True:
                    for _ in range(3):
                        await page.evaluate("window.scrollBy(0, 1000)")
                        await asyncio.sleep(random.uniform(0.7, 1.5))
                    await self.human_delay(3, 5)
                    new_height = await page.evaluate("document.documentElement.scrollHeight")
                    if new_height == last_height: break
                    last_height = new_height
                
                channels = await page.query_selector_all("#main-link")
                data = [{"Name": (await ch.inner_text()).strip(), "URL": f"https://www.youtube.com{await ch.get_attribute('href')}"} 
                        for ch in channels if await ch.get_attribute('href')]
                
                with open(SUBS_FILE, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["Name", "URL"])
                    writer.writeheader()
                    writer.writerows(data)
                
                self.log(f"🎉 백업 완료! {len(data)}개 채널 저장됨", "green")
                await context.close()
        except Exception as ex: self.log(f"중단됨: {ex}", "red")
        self.progress_bar.visible = False
        self.page.update()

    async def on_clear_click(self, e):
        async def start_clear(e):
            confirm_dlg.open = False
            self.log("--- 구독 취소 자동화 시작 ---", "red")
            self.progress_bar.visible = True
            self.page.update()
            try:
                async with async_playwright() as p:
                    context = await self.get_browser_context(p)
                    page = await context.new_page()
                    await self.ensure_logged_in_and_navigate(page, "https://www.youtube.com/feed/channels")
                    count = 0
                    while True:
                        btns = await page.query_selector_all('button:has-text("구독중")')
                        if not btns: break
                        for btn in btns:
                            try:
                                await btn.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(1, 2))
                                await btn.click()
                                confirm = await page.wait_for_selector('yt-button-renderer:has-text("구독 취소")', timeout=5000)
                                await confirm.click()
                                count += 1
                                self.log(f"취소됨 ({count}개째)...")
                                await self.human_delay(3.5, 6.5)
                                if count % 10 == 0:
                                    self.log("안전 휴식 중...", "white60")
                                    await self.human_delay(10, 15)
                            except: continue
                        await page.reload()
                        await self.human_delay(4, 7)
                    self.log(f"🎉 모든 작업 완료! 총 {count}개 취소됨", "green")
                    await context.close()
            except Exception as ex: self.log(f"중단됨: {ex}", "red")
            self.progress_bar.visible = False
            self.page.update()
        
        confirm_dlg = ft.AlertDialog(title=ft.Text("정말 삭제하시겠습니까?"), actions=[
            ft.TextButton("삭제 시작", on_click=start_clear, font_color="red"),
            ft.TextButton("취소", on_click=lambda _: setattr(confirm_dlg, "open", False) or self.page.update()),
        ])
        self.page.overlay.append(confirm_dlg)
        confirm_dlg.open = True
        self.page.update()

    async def on_import_click(self, e):
        if not SUBS_FILE.exists():
            self.log("파일이 없습니다!", "red")
            return
        self.log("--- 구독 복원 자동화 시작 ---", "green")
        self.progress_bar.visible = True
        self.page.update()
        try:
            async with async_playwright() as p:
                context = await self.get_browser_context(p)
                page = await context.new_page()
                with open(SUBS_FILE, "r", encoding="utf-8") as f:
                    reader = list(csv.DictReader(f))
                for i, row in enumerate(reader):
                    self.progress_bar.value = (i + 1) / len(reader)
                    self.status_text.value = f"진행: {int(self.progress_bar.value*100)}% ({i+1}/{len(reader)})"
                    self.page.update()
                    try:
                        await page.goto(row['URL'])
                        if i == 0 and ("accounts.google.com" in page.url or await page.query_selector('a:has-text("로그인")')):
                            if self.bg_switch.value: raise Exception("Login Required")
                            self.log("⚠️ 로그인이 필요합니다.", "yellow")
                            await page.wait_for_url(lambda url: "youtube.com" in url and "google.com" not in url, timeout=0)
                            await page.goto(row['URL'])
                        
                        btn = await page.wait_for_selector('button:has-text("구독"), button:has-text("Subscribe")', timeout=5000)
                        if "구독중" not in await btn.inner_text():
                            await btn.click()
                            self.log(f"✅ 구독 성공: {row['Name']}")
                            await self.human_delay(5, 8)
                        else:
                            self.log(f"이미 구독 중: {row['Name']}", "white60")
                            await self.human_delay(2, 3)
                        if (i + 1) % 5 == 0:
                            self.log("안전 휴식 중...", "white60")
                            await self.human_delay(8, 12)
                    except Exception as ex:
                        if str(ex) == "Login Required": raise ex
                        self.log(f"❌ 실패: {row['Name']}", "red")
                self.log("🎉 모든 복원 완료!", "green")
                await context.close()
        except Exception as ex: self.log(f"중단됨: {ex}", "red")
        self.progress_bar.visible = False
        self.page.update()

async def main(page: ft.Page):
    app_instance = YTManagerApp(page)
    await asyncio.sleep(0.1)
    app_instance.apply_window_settings()

def app():
    ft.run(main)

if __name__ == "__main__":
    app()
