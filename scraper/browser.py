import asyncio
import contextlib
import json
import os
import random
from pathlib import Path
from typing import Iterator, Optional

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from scraper.selectors import TIMEOUTS


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]


@contextlib.contextmanager
def launch_browser(headless: bool = True) -> Iterator[tuple[Playwright, Browser, BrowserContext]]:
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=headless,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process'
        ]
    )
    user_agent = random.choice(USER_AGENTS)

    # Configure proxy from environment if available
    proxy_config = None
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if https_proxy:
        proxy_config = {"server": https_proxy}

    context = browser.new_context(
        user_agent=user_agent,
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
        proxy=proxy_config
    )
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
    """
    Create a new page with configured default timeout.

    Args:
        context: Browser context to create page in

    Returns:
        Configured page instance
    """
    page = context.new_page()
    page.set_default_timeout(TIMEOUTS["default"])
    return page
