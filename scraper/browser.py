import asyncio
import contextlib
import json
import random
from pathlib import Path
from typing import Iterator, Optional

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]


@contextlib.contextmanager
def launch_browser(headless: bool = True) -> Iterator[tuple[Playwright, Browser, BrowserContext]]:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    user_agent = random.choice(USER_AGENTS)
    context = browser.new_context(user_agent=user_agent, viewport={"width": 1280, "height": 720})
    add_stealth(context)
    try:
        yield playwright, browser, context
    finally:
        context.close()
        browser.close()
        playwright.stop()


def add_stealth(context: BrowserContext) -> None:
    """Apply basic stealth scripts to the context."""
    context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """
    )


def new_page(context: BrowserContext) -> Page:
    page = context.new_page()
    page.set_default_timeout(10_000)
    return page
