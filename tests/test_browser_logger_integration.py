import pytest
from camouchat_core import Platform
from camouchat_browser import ProfileManager


def test_profile_manager_creation_log(caplog):
    """Verify that ProfileManager logs with the correct profile context."""
    import logging

    root_val = logging.getLogger("camouchat")
    root_val.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger="camouchat")

    import time

    pm = ProfileManager()
    profile_id = f"LogTest_{int(time.time())}"

    # We create a profile which triggers a log
    pm.create_profile(platform=Platform.WHATSAPP, profile_id=profile_id)

    # Check the record attributes
    assert any(profile_id in r.message for r in caplog.records)
    record = [r for r in caplog.records if profile_id in r.message][0]
    assert record.profile_id == profile_id
    assert record.platform == "BROWSER"


if __name__ == "__main__":
    pytest.main([__file__])
