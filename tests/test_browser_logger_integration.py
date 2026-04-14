import pytest
from camouchat_core import Platform
from camouchat_browser import ProfileManager

def test_profile_manager_creation_log(caplog):
    """Verify that ProfileManager logs with the correct profile context."""
    import logging
    caplog.set_level(logging.INFO)
    pm = ProfileManager()
    profile_id = "LoggerTestProfile_Cap"
    
    # We create a profile which triggers a log
    pm.create_profile(platform=Platform.WHATSAPP, profile_id=profile_id)
    
    # Check the record attributes
    record = caplog.records[-1]
    assert record.profile_id == profile_id
    assert record.platform == "BROWSER"

if __name__ == "__main__":
    pytest.main([__file__])
