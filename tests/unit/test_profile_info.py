import pytest
from pathlib import Path
from camouchat_core import Platform
from camouchat_browser.profile_info import ProfileInfo

def test_profile_info_serialization():
    data = {
        "profile_id": "test",
        "platform": Platform.WHATSAPP,
        "version": "1.0",
        "created_at": "now",
        "last_used": "now",
        "profile_dir": Path("/tmp/p"),
        "fingerprint_path": Path("/tmp/f"),
        "cache_dir": Path("/tmp/c"),
        "media_dir": Path("/tmp/m"),
        "media_images_dir": Path("/tmp/mi"),
        "media_videos_dir": Path("/tmp/mv"),
        "media_voice_dir": Path("/tmp/mvo"),
        "media_documents_dir": Path("/tmp/md"),
        "database_path": Path("/tmp/db"),
        "db_type": "sqlite",
        "username": "u",
        "password": "p",
        "host": "h",
        "port": 1234,
        "database_name": "db",
        "is_active": True,
        "last_active_pid": 123,
        "encryption": {"enabled": False}
    }
    info = ProfileInfo(**data)
    
    d = info.to_dict()
    assert d["profile_id"] == "test"
    assert d["platform"] == Platform.WHATSAPP
    
    s = str(info)
    assert "'profile_id': 'test'" in s
    
    r = repr(info)
    assert "ProfileInfo({" in r
    assert "'profile_id': 'test'" in r
