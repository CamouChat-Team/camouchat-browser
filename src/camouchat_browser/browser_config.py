"""
CamouBrowser Config.
Pass this config to the CamouBrowser
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from .browser_logger import logger
from camouchat_core import Platform


@dataclass
class BrowserConfig:
    """
    Config dataclass for browser.
    """

    platform: Platform
    locale: str
    enable_cache: bool
    headless: bool
    fingerprint: Optional[Any] = None
    geoip: bool = False
    proxy: Optional[Dict[str, str]] = None
    prefs: Optional[Dict[str, bool]] = None
    addons: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> BrowserConfig:
        """
        Creates a BrowserConfig instance from a dictionary.

        Parameters:
            data (dict): Configuration object.

        Required:
            platform (Platform)
                Target platform enum.
                Example: Platform.WHATSAPP

        Optional:
            locale (str)
                Browser locale.
                Default: "en-US"

            enable_cache (bool)
                Enables browser cache.
                Default: False

            headless (bool)
                Runs browser in headless mode.
                Default: False

            geoip (bool)
                Enables GeoIP spoofing.
                Default: False

            proxy (dict)
                Proxy configuration.
                Format:
                    {
                        "server": "http://host:port",
                        "username": "user",
                        "password": "pass"
                    }

            prefs (dict)
                Browser preferences (always dict, never None).
                Example:
                    {
                        "javascript.enabled": True
                    }

            addons (list[str])
                List of absolute extension paths (always list).

            fingerprint (object)
                Fingerprint provider instance (e.g., BrowserForge).

        Raises:
            ValueError:
                - if data is missing/inccorect type
                - if platform is invalid/incorrect type
                - if proxy format is incorrect
        """
        if not data:
            raise ValueError("'data : dict' is required for creating BrowserConfig instance")

        platform = data.get("platform")
        if not platform:
            raise ValueError("'platform' is required for creating BrowserConfig instance")

        if not isinstance(platform, Platform):
            raise ValueError("'platform' must be an instance of Platform")

        locale = data.get("locale")
        if not locale:
            logger.warning("No locale provided, using default locale en-US")
            locale = "en-US"

        fingerprint = data.get("fingerprint")
        if not fingerprint:
            logger.debug("No fingerprint provided, using default fingerprint")

        proxy = data.get("proxy")

        if proxy is None:
            logger.warning("No proxy provided, using system network.")
        else:
            if not isinstance(proxy, dict):
                raise ValueError("proxy must be a dict")

            server = proxy.get("server")
            if not server or not isinstance(server, str):
                raise ValueError("proxy['server'] is required and must be a string")

            username = proxy.get("username")
            password = proxy.get("password")

            if (username and not password) or (password and not username):
                raise ValueError("proxy username/password must be provided together")

            if username and not isinstance(username, str):
                raise ValueError("proxy['username'] must be string")

            if password and not isinstance(password, str):
                raise ValueError("proxy['password'] must be string")

        prefs = data.get("prefs")
        if prefs is None:
            logger.debug("No prefs provided, using default prefs")
            prefs = {}
        elif not isinstance(prefs, dict):
            raise ValueError(f"prefs must be a dict, got {type(prefs)}")

        addons = data.get("addons")
        if addons is None:
            logger.debug("No addons provided, using Empty list for addons")
            addons = []
        elif not isinstance(addons, list):
            raise ValueError(f"addons must be a list, got {type(addons)}")
        else:
            if any(not isinstance(a, str) for a in addons):
                raise ValueError("all addons must be strings")

        enable_cache = data.get("enable_cache")
        if enable_cache is None:
            logger.debug("No enable_cache provided, using default enable_cache False")
            enable_cache = False

        headless = data.get("headless")
        if headless is None:
            logger.warning("No headless provided, using default headless False")
            headless = False

        geoip = data.get("geoip")
        if geoip is None:
            geoip = True if proxy else False
            logger.debug(f"No geoip provided, using auto geoip: {geoip}")

        return cls(
            platform=platform,
            locale=locale,
            enable_cache=enable_cache,
            headless=headless,
            prefs=prefs,
            addons=addons,
            fingerprint=fingerprint,
            geoip=geoip,
            proxy=proxy,
        )

    def __str__(self):
        return f"""
            Platform: {self.platform}
            Locale: {self.locale}
            EnableCache: {self.enable_cache}
            Headless: {self.headless}
            Fingerprint: {self.fingerprint!r} # Need to check for the fingerprint's __repr__
            geoip: {self.geoip}
            Proxy: {self.proxy}
            Preferences: {self.prefs}
            Addons: {self.addons}
            """

    def __repr__(self):
        return (
            f"BrowserConfig("
            f"platform={self.platform}, "
            f"locale='{self.locale}', "
            f"headless={self.headless}, "
            f"geoip={self.geoip}, "
            f"fingerprint={self.fingerprint!r}"
            f")"
        )

    def to_dict(self) -> Dict:
        """
        Serializes BrowserConfig to a dictionary.
        """
        return {
            "platform": self.platform,
            "locale": self.locale,
            "enable_cache": self.enable_cache,
            "headless": self.headless,
            "geoip": self.geoip,
            "proxy": self.proxy,
            "prefs": self.prefs,
            "addons": self.addons,
            "fingerprint": {"provider": "browserforge"},
        }
