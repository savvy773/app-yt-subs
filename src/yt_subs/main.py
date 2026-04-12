import asyncio
import csv
import json
import random
import sys
from typing import List, Any, cast
import flet as ft
from pathlib import Path
from playwright.async_api import async_playwright, Playwright

"""
YouTube Subscriptions Manager
Original Author: savvy773 (https://github.com/savvy773)
License: MIT
"""

# --- App Data Paths ---
import os
APP_DATA_DIR  = Path(os.environ.get("APPDATA", Path.home())) / "yt-subs"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

USER_DATA_DIR = APP_DATA_DIR / "user_data"
SUBS_FILE     = APP_DATA_DIR / "subscriptions.csv"
CONFIG_FILE   = APP_DATA_DIR / "config.json"
# ----------------------

class YTManagerApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "YouTube Subscriptions Manager by savvy773"
        self.page.theme_mode = ft.ThemeMode.DARK
        
        self.config = {"width": 600, "height": 900, "top": 100, "left": 100}
        self.load_config()
        self.apply_window_settings()
        
        # UI Elements
        self.log_area = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)
        self.progress_bar = ft.ProgressBar(width=500, visible=False)
        self.progress_bar.color = "blue"
        self.progress_bar.bgcolor = "#222222"
        self.progress_bar.value = 0
        self.status_text = ft.Text("Status: Waiting", color="white70")
        
        # Background Mode Switch
        self.bg_switch = ft.Switch(label="Background Mode (Hide Browser)", value=False, label_position=ft.LabelPosition.LEFT)
        
        self.setup_ui()

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    saved = json.load(f)
                    for k in self.config.keys():
                        if k in saved and saved[k] is not None: 
                            self.config[k] = saved[k]
            except: pass

    def save_config(self):
        try:
            w = self.page.window.width
            h = self.page.window.height
            t = self.page.window.top
            l = self.page.window.left
            
            if all(v is not None for v in [w, h, t, l]):
                self.config["width"] = int(w) if w else 600
                self.config["height"] = int(h) if h else 900
                self.config["top"] = int(t) if t else 100
                self.config["left"] = int(l) if l else 100
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.config, f)
        except: pass

    def apply_window_settings(self):
        self.page.window.width = self.config["width"]
        self.page.window.height = self.config["height"]
        self.page.window.top = self.config["top"]
        self.page.window.left = self.config["left"]
        self.page.update()

    async def _auto_save_loop(self):
        """Save window position and size every 2 seconds in the background."""
        while True:
            await asyncio.sleep(2)
            self.save_config()

    def setup_ui(self):
        header = ft.Column(controls=[
            ft.Text("YouTube Subscriptions", size=32, weight=ft.FontWeight.BOLD, color="blue"),
            ft.Text("Safe & Automated Management by savvy773", color="white70", size=14),
        ])
        
        # Step 1: Authentication
        # Replaced ElevatedButton with FilledButton to avoid DeprecationWarning
        auth_section = ft.Container(
            content=ft.Column([
                ft.Text("Step 1: Authentication", size=16, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.FilledButton(
                        "Login / Check Session", 
                        icon=ft.Icons.LOGIN, 
                        on_click=self.on_login_click,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE)
                    ),
                    self.bg_switch
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            padding=15,
            bgcolor="#222222",
            border_radius=10,
        )

        # Step 2: Actions
        action_buttons = ft.Row(
            controls=cast(List[ft.Control], [
                ft.FilledButton("Export (Backup)", icon=ft.Icons.DOWNLOAD, on_click=self.on_export_click, style=ft.ButtonStyle(bgcolor="blue700", color="white")),
                ft.FilledButton("Clear (Delete)", icon=ft.Icons.DELETE_FOREVER, on_click=self.on_clear_click, style=ft.ButtonStyle(bgcolor="red700", color="white")),
                ft.FilledButton("Import (Restore)", icon=ft.Icons.UPLOAD, on_click=self.on_import_click, style=ft.ButtonStyle(bgcolor="green700", color="white")),
            ]),
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        
        log_container = ft.Container(
            content=self.log_area, bgcolor="#1A1A1A", border_radius=10, padding=10, expand=True, border=ft.Border.all(1, "#333333")
        )
        
        footer = ft.Row(
            controls=[ft.Text("© 2026 savvy773. All rights reserved.", size=11, color="white24")],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        self.page.add(
            header, ft.Divider(height=20, color="transparent"),
            auth_section, ft.Divider(height=10, color="transparent"),
            ft.Text("Step 2: Subscriptions Management", size=16, weight=ft.FontWeight.BOLD),
            action_buttons, ft.Divider(height=30, color="#333333"),
            self.status_text, self.progress_bar, ft.Text("Real-time Logs", size=12, color="white40"),
            log_container,
            footer
        )

    def log(self, message: str, color: str = "white"):
        self.log_area.controls.append(ft.Text(message, color=color, size=13))
        self.page.update()

    async def get_browser_context(self, p: Playwright, force_visible: bool = False):
        if not USER_DATA_DIR.exists(): USER_DATA_DIR.mkdir(parents=True)
        headless = False if force_visible else self.bg_switch.value
        
        if headless:
            self.log("💡 Background Mode: Running browser hidden.", "white60")
        
        return await p.chromium.launch_persistent_context(
            str(USER_DATA_DIR), 
            headless=headless, 
            channel="chrome",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            ignore_default_args=["--enable-automation"],
            args=["--start-maximized", "--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-infobars"]
        )

    async def human_delay(self, min_sec: float = 2.5, max_sec: float = 5.0):
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def ensure_logged_in_and_navigate(self, page, target_url: str):
        self.log("Checking Google environment...", "white60")
        try:
            await page.goto("https://www.google.com")
        except Exception:
            self.log("❌ Error: Could not load browser. Make sure Chromium is installed.", "red")
            self.log("Run 'playwright install chromium' in terminal.", "yellow")
            raise

        await asyncio.sleep(2)
        await page.goto(target_url)
        
        if "accounts.google.com" in page.url or await page.query_selector('a:has-text("Sign in"), a:has-text("로그인")'):
            if self.bg_switch.value:
                self.log("❌ Error: Login required! Disable Background Mode and log in first.", "red")
                raise Exception("Login Required")
            
            self.log("⚠️ Login required. Please complete login in the browser window!", "yellow")
            await page.wait_for_url(lambda url: "youtube.com" in url and "google.com" not in url, timeout=0)
            self.log("✅ Login confirmed! Resuming automation.", "green")
            await self.human_delay(3, 5)
            await page.goto(target_url)
        else:
            self.log("✅ Login state verified.", "green")

    async def on_login_click(self, e: Any):
        self.log("--- Login / Session Check ---", "blue")
        try:
            async with async_playwright() as p:
                context = await self.get_browser_context(p, force_visible=True)
                page = await context.new_page()
                self.log("Opening YouTube...")
                await page.goto("https://www.youtube.com/feed/channels")
                
                if "accounts.google.com" in page.url or await page.query_selector('a:has-text("Sign in"), a:has-text("로그인")'):
                    self.log("⚠️ Not logged in. Please log in manually in the browser window.", "yellow")
                    await page.wait_for_url(lambda url: "youtube.com" in url and "google.com" not in url, timeout=0)
                    self.log("✅ Login successful!", "green")
                else:
                    self.log("✅ You are already logged in.", "green")
                
                await asyncio.sleep(2)
                await context.close()
                self.log("Browser closed. You can now use Background Mode.", "white60")
        except Exception as ex:
            self.log(f"Login failed or cancelled: {ex}", "red")

    async def on_export_click(self, e: Any):
        self.log("--- Export Process Started ---", "blue")
        self.progress_bar.visible, self.progress_bar.value = True, None
        self.page.update()
        try:
            async with async_playwright() as p:
                context = await self.get_browser_context(p)
                page = await context.new_page()
                await self.ensure_logged_in_and_navigate(page, "https://www.youtube.com/feed/channels")
                
                self.log("Scanning channels... (This may take a while)")
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
                
                self.log(f"🎉 Success! {len(data)} channels exported.", "green")
                await context.close()
        except Exception as ex: self.log(f"Process stopped: {ex}", "red")
        self.progress_bar.visible = False
        self.page.update()

    async def on_clear_click(self, e: Any):
        async def start_clear(e_clear: Any):
            confirm_dlg.open = False
            self.log("--- Unsubscribe Process Started ---", "red")
            self.progress_bar.visible = True
            self.page.update()
            try:
                async with async_playwright() as p:
                    context = await self.get_browser_context(p)
                    page = await context.new_page()
                    await self.ensure_logged_in_and_navigate(page, "https://www.youtube.com/feed/channels")
                    count = 0
                    while True:
                        btns = await page.query_selector_all('button:has-text("Subscribed"), button:has-text("구독중")')
                        if not btns: break
                        for btn in btns:
                            try:
                                await btn.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(1, 2))
                                await btn.click()
                                confirm = await page.wait_for_selector('yt-button-renderer:has-text("Unsubscribe"), yt-button-renderer:has-text("구독 취소")', timeout=5000)
                                if confirm:
                                    await confirm.click()
                                    count += 1
                                    self.log(f"Unsubscribed ({count})...")
                                    await self.human_delay(3.5, 6.5)
                                    if count % 10 == 0:
                                        self.log("Safe break for account protection...", "white60")
                                        await self.human_delay(10, 15)
                            except: continue
                        await page.reload()
                        await self.human_delay(4, 7)
                    self.log(f"🎉 Finished! {count} subscriptions removed.", "green")
                    await context.close()
            except Exception as ex: self.log(f"Process stopped: {ex}", "red")
            self.progress_bar.visible = False
            self.page.update()
        
        confirm_dlg_actions = cast(List[ft.Control], [
            ft.TextButton("Confirm", on_click=start_clear, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ft.TextButton("Cancel", on_click=lambda _: setattr(confirm_dlg, "open", False) or self.page.update()),
        ])
        confirm_dlg = ft.AlertDialog(title=ft.Text("Confirm Mass Unsubscribe?"), actions=confirm_dlg_actions)
        self.page.overlay.append(confirm_dlg)
        confirm_dlg.open = True
        self.page.update()

    async def on_import_click(self, e: Any):
        if not SUBS_FILE.exists():
            self.log("Backup file (subscriptions.csv) not found!", "red")
            return
        self.log("--- Import Process Started ---", "green")
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
                    self.status_text.value = f"Progress: {int(self.progress_bar.value*100)}% ({i+1}/{len(reader)})"
                    self.page.update()
                    try:
                        await page.goto(row['URL'])
                        if i == 0 and ("accounts.google.com" in page.url or await page.query_selector('a:has-text("Sign in"), a:has-text("로그인")')):
                            if self.bg_switch.value: raise Exception("Login Required")
                            self.log("⚠️ Login required.", "yellow")
                            await page.wait_for_url(lambda url: "youtube.com" in url and "google.com" not in url, timeout=0)
                            await page.goto(row['URL'])
                        
                        btn = await page.wait_for_selector('button:has-text("Subscribe"), button:has-text("구독")', timeout=5000)
                        if btn:
                            btn_text = await btn.inner_text()
                            if "Subscribed" not in btn_text and "구독중" not in btn_text:
                                await btn.click()
                                self.log(f"✅ Subscribed: {row['Name']}")
                                await self.human_delay(5, 8)
                            else:
                                self.log(f"Already Subscribed: {row['Name']}", "white60")
                                await self.human_delay(2, 3)
                        if (i + 1) % 5 == 0:
                            self.log("Safe break for account protection...", "white60")
                            await self.human_delay(8, 12)
                    except Exception as ex:
                        if str(ex) == "Login Required": raise ex
                        self.log(f"❌ Failed: {row['Name']}", "red")
                self.log("🎉 All restore operations completed!", "green")
                await context.close()
        except Exception as ex: self.log(f"Process stopped: {ex}", "red")
        self.progress_bar.visible = False
        self.page.update()

async def main(page: ft.Page):
    app_instance = YTManagerApp(page)
    await asyncio.sleep(0.1)
    app_instance.apply_window_settings()
    asyncio.create_task(app_instance._auto_save_loop())

def app():
    ft.run(main)

if __name__ == "__main__":
    app()
