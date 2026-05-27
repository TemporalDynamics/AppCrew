import json
import os
import random
from pathlib import Path

import yaml


class BrowserManager:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.session_file = Path(self.config["linkedin"]["session_file"])
        self.user_agent = self.config["linkedin"]["user_agent"]
        self._browser = None
        self._context = None

    @property
    def is_authenticated(self) -> bool:
        return self.session_file.exists()

    async def launch(self):
        from playwright.async_api import async_playwright

        if self._browser:
            return self._browser

        p = await async_playwright().start()
        self._browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        storage = None
        if self.is_authenticated:
            storage = json.loads(self.session_file.read_text())

        self._context = await self._browser.new_context(
            storage_state=storage,
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
        )

        if storage:
            await self._context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

        return self._browser

    async def get_page(self):
        if not self._context:
            await self.launch()
        page = await self._context.new_page()
        return page

    async def save_session(self):
        if self._context:
            state = await self._context.storage_state()
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            self.session_file.write_text(json.dumps(state, indent=2))

    async def human_delay(self, page, min_s: float = 2.0, max_s: float = 7.0):
        delay = random.uniform(min_s, max_s)
        await page.wait_for_timeout(delay * 1000)

    async def close(self):
        if self._browser:
            await self._browser.close()

    def get_status(self) -> dict:
        return {
            "authenticated": self.is_authenticated,
            "session_file": str(self.session_file) if self.is_authenticated else None,
        }
