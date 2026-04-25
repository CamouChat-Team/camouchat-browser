import json
import os
from unittest.mock import MagicMock, patch

import pytest
from camouchat_core import Platform

from camouchat_browser.profile_info import ProfileInfo
from camouchat_browser.profile_manager import ProfileManager


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def profile_manager(temp_dir):
    with patch("camouchat_browser.directory.PlatformDirs") as mock_dirs:
        mock_dirs.return_value.user_data_dir = str(temp_dir / "data")
        mock_dirs.return_value.user_cache_dir = str(temp_dir / "cache")
        mock_dirs.return_value.user_log_dir = str(temp_dir / "logs")
        pm = ProfileManager()
        return pm


def test_profile_manager_lifecycle(profile_manager):
    # Test Create
    profile = profile_manager.create_profile(Platform.WHATSAPP, "test_p")
    assert profile.profile_id == "test_p"
    assert profile.platform == Platform.WHATSAPP
    assert profile_manager.is_profile_exists(Platform.WHATSAPP, "test_p")

    # Test Create Duplicate (idempotent)
    profile2 = profile_manager.create_profile(Platform.WHATSAPP, "test_p")
    assert profile2.profile_id == "test_p"

    # Test Get
    profile3 = profile_manager.get_profile(Platform.WHATSAPP, "test_p")
    assert profile3.profile_id == "test_p"

    # Test List
    listing = profile_manager.list_profiles(Platform.WHATSAPP)
    assert "test_p" in listing[Platform.WHATSAPP]

    listing_all = profile_manager.list_profiles()
    assert "whatsapp" in listing_all
    assert "test_p" in listing_all["whatsapp"]

    # Test Delete
    profile_manager.delete_profile(profile)
    assert not profile_manager.is_profile_exists(Platform.WHATSAPP, "test_p")


def test_profile_manager_encryption(profile_manager):
    profile_id = "enc_profile"
    profile_manager.create_profile(Platform.WHATSAPP, profile_id)

    # Enable Encryption
    profile_manager.enable_encryption(Platform.WHATSAPP, profile_id)
    assert profile_manager.is_encryption_enabled(Platform.WHATSAPP, profile_id)

    # Get Key
    key = profile_manager.get_key(Platform.WHATSAPP, profile_id)
    assert isinstance(key, bytes)
    assert len(key) == 32

    # Re-enable should fail
    with pytest.raises(ValueError, match="already enabled"):
        profile_manager.enable_encryption(Platform.WHATSAPP, profile_id)

    # Disable Encryption
    profile_manager.disable_encryption(Platform.WHATSAPP, profile_id)
    assert not profile_manager.is_encryption_enabled(Platform.WHATSAPP, profile_id)

    # Get Key after disable should fail
    with pytest.raises(ValueError, match="not enabled"):
        profile_manager.get_key(Platform.WHATSAPP, profile_id)


def test_profile_manager_encryption_errors(profile_manager):
    profile_id = "err_profile"
    profile_manager.create_profile(Platform.WHATSAPP, profile_id)

    with pytest.raises(ValueError, match="not enabled"):
        profile_manager.disable_encryption(Platform.WHATSAPP, profile_id)

    # Manually enable in metadata but delete key file
    metadata_path = (
        profile_manager.directory.get_profile_dir(Platform.WHATSAPP, profile_id) / "metadata.json"
    )
    with open(metadata_path) as f:
        data = json.load(f)
    data["encryption"]["enabled"] = True
    with open(metadata_path, "w") as f:
        json.dump(data, f)

    key_file_path = profile_manager.directory.get_key_file_path(Platform.WHATSAPP, profile_id)
    if key_file_path.exists():
        key_file_path.unlink()

    with pytest.raises(FileNotFoundError, match="Encryption key file missing"):
        profile_manager.get_key(Platform.WHATSAPP, profile_id)


def test_profile_manager_pid_alive():
    assert not ProfileManager.is_pid_alive(0)
    assert not ProfileManager.is_pid_alive(-1)
    # Current PID should be alive
    assert ProfileManager.is_pid_alive(os.getpid())
    # Very high PID likely doesn't exist
    assert not ProfileManager.is_pid_alive(999999)


def test_profile_manager_activate_deactivate(profile_manager):
    profile_id = "act_profile"
    profile_manager.create_profile(Platform.WHATSAPP, profile_id)

    mock_browser = MagicMock()
    mock_browser.config = MagicMock()

    # Activate
    profile_manager.activate_profile(Platform.WHATSAPP, profile_id, mock_browser)
    assert profile_manager.__p_count__() == 1

    # Activate again should fail if PID is alive (it is, since we set it to current pid)
    with pytest.raises(RuntimeError, match="Profile already active"):
        profile_manager.activate_profile(Platform.WHATSAPP, profile_id, mock_browser)

    # Test headless force when multiple profiles
    mock_browser_2 = MagicMock()
    mock_browser_2.config = MagicMock()
    mock_browser_2.config.headless = False

    profile_manager.create_profile(Platform.WHATSAPP, "other_profile")
    profile_manager.activate_profile(Platform.WHATSAPP, "other_profile", mock_browser_2)
    assert mock_browser_2.config.headless is True


def test_profile_manager_errors(profile_manager):
    with pytest.raises(ValueError, match="Profile metadata not found"):
        profile_manager.get_profile(Platform.WHATSAPP, "non_existent")

    with pytest.raises(ValueError, match="does not exist"):
        mock_profile = MagicMock(spec=ProfileInfo)
        mock_profile.profile_id = "none"
        mock_profile.platform = Platform.WHATSAPP
        profile_manager.delete_profile(mock_profile)


@pytest.mark.asyncio
async def test_close_profile_simple(profile_manager):
    profile_id = "close_p"
    profile = profile_manager.create_profile(Platform.WHATSAPP, profile_id)

    # Mock activate manually to avoid side effects
    metadata = profile_manager._read_metadata(Platform.WHATSAPP, profile_id)
    metadata["status"]["is_active"] = True
    metadata["status"]["last_active_pid"] = os.getpid()
    profile_manager._write_metadata(Platform.WHATSAPP, profile_id, metadata)
    profile_manager.__inc__()

    with patch(
        "camouchat_browser.camoufox_browser.CamoufoxBrowser.close_browser_by_profile"
    ) as mock_close:
        mock_close.return_value = True
        await profile_manager.close_profile(profile)

    metadata = profile_manager._read_metadata(Platform.WHATSAPP, profile_id)
    assert not metadata["status"]["is_active"]
    assert metadata["status"]["last_active_pid"] is None


def test_profile_manager_metadata_corruption(profile_manager):
    profile_id = "corrupt_p"
    profile_manager.create_profile(Platform.WHATSAPP, profile_id)

    metadata_file = (
        profile_manager.directory.get_profile_dir(Platform.WHATSAPP, profile_id) / "metadata.json"
    )
    with open(metadata_file, "w") as f:
        json.dump({"status": {"is_active": False}}, f)  # Missing "paths"

    mock_browser = MagicMock()
    with pytest.raises(ValueError, match="Corrupted metadata file"):
        profile_manager.activate_profile(Platform.WHATSAPP, profile_id, mock_browser)


def test_profile_manager_delete_active(profile_manager):
    profile_id = "active_del"
    profile = profile_manager.create_profile(Platform.WHATSAPP, profile_id)

    metadata = profile_manager._read_metadata(Platform.WHATSAPP, profile_id)
    metadata["status"]["is_active"] = True
    profile_manager._write_metadata(Platform.WHATSAPP, profile_id, metadata)

    with pytest.raises(ValueError, match="Cannot delete active profile"):
        profile_manager.delete_profile(profile)

    # Force delete should work
    profile_manager.delete_profile(profile, force=True)
    assert not profile_manager.is_profile_exists(Platform.WHATSAPP, profile_id)
