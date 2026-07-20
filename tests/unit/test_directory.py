import pytest
from unittest.mock import patch
from camouchat_browser.directory import DirectoryManager

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path

@pytest.fixture
def directory_manager(temp_dir):
    with patch("camouchat_browser.directory.PlatformDirs") as mock_dirs:
        mock_dirs.return_value.user_data_dir = str(temp_dir / "data")
        mock_dirs.return_value.user_cache_dir = str(temp_dir / "cache")
        mock_dirs.return_value.user_log_dir = str(temp_dir / "logs")
        return DirectoryManager()

def test_directory_manager_paths(directory_manager):
    assert directory_manager.get_platform_dir("WHATSAPP").name == "whatsapp"
    assert directory_manager.get_profile_dir("WHATSAPP", "p1").name == "p1"
    
    # Create dirs so touch works
    directory_manager.get_platform_dir("WHATSAPP").mkdir(parents=True, exist_ok=True)
    directory_manager.get_profile_dir("WHATSAPP", "p1").mkdir(parents=True, exist_ok=True)
    
    db_path = directory_manager.get_database_path("WHATSAPP", "p1")
    assert db_path.name == "messages.db"
    assert db_path.exists()
    
    db_path_custom = directory_manager.get_database_path("WHATSAPP", "p1", "test.db")
    assert db_path_custom.name == "test.db"
    assert db_path_custom.exists()
    
    assert directory_manager.get_error_trace_file().name == "ErrorTrace.log"
    assert directory_manager.get_browser_log_file().name == "browser.log"
    
    assert directory_manager.get_cache_root() == directory_manager.cache_dir
    assert directory_manager.get_log_root() == directory_manager.log_dir

def test_directory_manager_profile_subs(directory_manager):
    p = "WHATSAPP"
    id = "p1"
    assert directory_manager.get_cache_dir(p, id).name == "cache"
    assert directory_manager.get_backup_dir(p, id).name == "backups"
    assert directory_manager.get_media_dir(p, id).name == "media"
    assert directory_manager.get_media_images_dir(p, id).name == "images"
    assert directory_manager.get_media_videos_dir(p, id).name == "videos"
    assert directory_manager.get_media_voice_dir(p, id).name == "voice"
    assert directory_manager.get_media_documents_dir(p, id).name == "documents"
