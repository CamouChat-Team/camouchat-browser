"""
Test ProfileManager.
"""

import asyncio

from camouchat_core import Platform

from camouchat_browser import (
    BrowserConfig,
    BrowserForge,
    CamoufoxBrowser,
    ProfileManager,
)

# ── Profile  ─────────────────────────────────────────────────────────────
pm = ProfileManager()
work = pm.create_profile(platform=Platform.WHATSAPP, profile_id="work")

# ── Browser ─────────────────────────────────────────────────────────────

browser_forge = BrowserForge()
config = BrowserConfig.from_dict(
    {
        "platform": Platform.WHATSAPP,
        "locale": "en-US",
        "enable_cache": False,
        "headless": False,
        "geoip": False,
    }
)


async def main():
    browser = CamoufoxBrowser(profile=work, config=config)
    page = await browser.get_page()  # Get the page of the browser.
    print("navigating to whatsapp web...")
    await page.goto("https://web.whatsapp.com/")
    print("sleeping for 5 sec..")
    await asyncio.sleep(5)
    print("End Reached , can safely close the browser now...")
    await pm.close_profile(profile=work)
    pm.delete_profile(profile=work)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback

        traceback.print_exc()
