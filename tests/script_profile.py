"""
Test ProfileManager.
"""

import asyncio

from camouchat_core import Platform

from camouchat_browser import ProfileManager
from camouchat_browser.browser_logger import get_profile_browser_logger
from camouchat_browser import BrowserConfig, BrowserForge, CamoufoxBrowser

logger = get_profile_browser_logger(name=__name__, profile_id="test_script")
# ── Profile  ─────────────────────────────────────────────────────────────
pm = ProfileManager()
work = pm.create_profile(platform=Platform.WHATSAPP, profile_id="work")
# StorageType default used = SQLITE , database_url kept default.

# ── Browser ─────────────────────────────────────────────────────────────

browser_forge = BrowserForge(log=logger)
config = BrowserConfig.from_dict(
    {
        "platform": Platform.WHATSAPP,
        "locale": "en-US",
        "enable_cache": False,
        "headless": False,
        "fingerprint_obj": browser_forge,
        "geoip": False,
    }
)


async def main():
    browser = CamoufoxBrowser(profile=work, config=config, log=logger)
    page = await browser.get_page()  # Get the page of the browser.
    print("navigating to whatsapp web...")
    await page.goto("https://web.whatsapp.com/")
    print("sleeping for 10 sec..")
    await asyncio.sleep(10)
    print("End Reached , can safely close the browser now...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback

        traceback.print_exc()
