"""
CamouChat Browser Plugin.

This package provides high-performance, stealth-oriented browser management
for the CamouChat ecosystem, leveraging Camoufox and BrowserForge for
advanced anti-detection and session isolation.
"""

from .browser_config import BrowserConfig
from .browserforge import BrowserForge
from .camoufox_browser import CamoufoxBrowser
from .directory import DirectoryManager
from .exceptions import BrowserException
from .profile_info import ProfileInfo
from .profile_manager import ProfileManager

# Todo , adding logger later

__all__ = [
    "BrowserForge",
    "BrowserConfig",
    "DirectoryManager",
    "ProfileInfo",
    "ProfileManager",
    "CamoufoxBrowser",
    "BrowserException",
]
