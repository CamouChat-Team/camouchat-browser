from camouchat_core import LoggerFactory


def get_profile_browser_logger(
    name: str, profile_id: str = "GLOBAL", level: int | str | None = None
):
    """Returns a logger specialized for browser operations with profile context."""
    return LoggerFactory.get_logger(
        name=name, platform="BROWSER", profile_id=profile_id, level=level
    )


# Default logger for the module
logger = get_profile_browser_logger("browser_init")
