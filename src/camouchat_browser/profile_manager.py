"""
Profile lifecycle and encryption management.

This module coordinates the creation, activation, and deletion of browser
profiles, ensuring session isolation and secure storage of encryption keys.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
from datetime import datetime, timezone
from logging import Logger, LoggerAdapter
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from camouchat_core import KeyManager, Platform

from .browser_logger import get_profile_browser_logger, logger
from .camoufox_browser import CamoufoxBrowser
from .directory import DirectoryManager
from .profile_info import ProfileInfo


class ProfileManager:
    """
    Orchestrates the lifecycle and security of browser profiles.

    Each profile represents a unique execution environment with isolated:
    - Metadata: Configuration and state tracking.
    - Encryption: AES-256 keys for secure database storage.
    - Session Data: Cookies, cache, and local storage via Camoufox.
    - Identity: Hardware fingerprints via BrowserForge.
    """

    p_count: int = 0

    def __init__(self, log: Optional[Union[LoggerAdapter, Logger]] = None) -> None:
        self.directory = DirectoryManager()
        self.log = log or logger

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_metadata(
        self, platform: Platform, profile_id: str, db_credentials: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """
        Generates metadata for a new profile.

        Args:
            platform: The platform for which to generate metadata.
            profile_id: The ID of the profile for which to generate metadata.
            db_credentials: Database credentials.

        Returns:
            A dictionary containing the metadata for the profile.
        """
        now = datetime.now(timezone.utc).isoformat()

        profile_dir = self.directory.get_profile_dir(platform, profile_id)
        fingerprint_file_path = self.directory.get_fingerprint_file_path(
            platform, profile_id
        )
        cache_dir = self.directory.get_cache_dir(platform, profile_id)
        media_dir = self.directory.get_media_dir(platform, profile_id)
        media_images_dir = self.directory.get_media_images_dir(platform, profile_id)
        media_videos_dir = self.directory.get_media_videos_dir(platform, profile_id)
        media_voice_dir = self.directory.get_media_voice_dir(platform, profile_id)
        media_documents_dir = self.directory.get_media_documents_dir(
            platform, profile_id
        )
        key_file_path = self.directory.get_key_file_path(platform, profile_id)

        encryption: Dict[str, Any] = {
            "enabled": False,
            "algorithm": "AES-256-GCM",
            "key_file": str(key_file_path),
            "created_at": None,
        }
        self.log.debug(
            f"Generated metadata for profile [{profile_id}] on platform [{platform}]"
        )

        return {
            "profile_id": profile_id,
            "platform": platform,
            "version": "0.6",
            "created_at": now,
            "last_used": now,
            "database": db_credentials,
            "paths": {
                "profile_dir": str(profile_dir),
                "fingerprint_file": str(fingerprint_file_path),
                "cache_dir": str(cache_dir),
                "media_dir": str(media_dir),
                "media_images": str(media_images_dir),
                "media_videos": str(media_videos_dir),
                "media_voice": str(media_voice_dir),
                "media_documents": str(media_documents_dir),
            },
            "encryption": encryption,
            "status": {
                "is_active": False,
                "last_active_pid": None,
                "lock_file": ".lock",
            },
        }

    def _read_metadata(self, platform: Platform, profile_id: str) -> Dict[str, Any]:
        profile_dir = self.directory.get_profile_dir(platform, profile_id)
        metadata_file = profile_dir / "metadata.json"
        if not metadata_file.exists():
            raise ValueError(
                f"Profile metadata not found for '{profile_id}' on '{platform}'."
            )
        with open(metadata_file) as f:
            return json.load(f)

    def _write_metadata(
        self, platform: Platform, profile_id: str, data: Dict[str, Any]
    ) -> None:
        profile_dir = self.directory.get_profile_dir(platform, profile_id)
        with open(profile_dir / "metadata.json", "w") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def __inc__(cls):
        cls.p_count += 1

    @classmethod
    def __dec__(cls):
        if cls.p_count > 0:
            cls.p_count -= 1

    @classmethod
    def __p_count__(cls):
        return cls.p_count

    # ------------------------------------------------------------------
    # Profile lifecycle
    # ------------------------------------------------------------------

    def create_profile(
        self, platform: Platform, profile_id: str, db_credentials: Dict[str, Any] = {}
    ) -> ProfileInfo:
        """
        Create a new profile; returns the existing one if already present.

        args :
        -platform : Platform must use from camouchat-core
        -profile_id : id/name of the profile to create

        - db_credentials : Dict[str , Any] = {}
            - storage_type : type of storage must use from camouchat-core's StorageType
            - username : username of the database
            - password : password of the database
            - host : host of the database
            - port : port of the database
            - database_name : name of the database

        :return - ProfileInfo object
        """
        profile_dir = self.directory.get_profile_dir(platform, profile_id)
        p_log = get_profile_browser_logger(name="ProfileManager", profile_id=profile_id)

        metadata_file = profile_dir / "metadata.json"

        if profile_dir.exists() and metadata_file.exists():
            p_log.info(f"Skiping, profile exists with name [{profile_id}]")
            return self.get_profile(platform, profile_id)
        else:
            self.directory.setup_profile_directories(platform, profile_id)

        # sanitize db_credentials
        if not db_credentials:
            db_credentials = {
                "storage_type": None,
                "username": None,
                "password": None,
                "host": None,
                "port": None,
                "database_name": None,
            }
        db_credentials["database_path"] = str(
            self.directory.get_database_path(platform, profile_id)
        )

        metadata = self._generate_metadata(
            platform=platform, profile_id=profile_id, db_credentials=db_credentials
        )
        self._write_metadata(platform, profile_id, metadata)

        p_log.info(
            f"Profile created with name [{profile_id}] & stored at [{profile_dir}]"
        )
        return ProfileInfo.from_metadata(metadata)

    def get_profile(self, platform: Platform, profile_id: str) -> ProfileInfo:
        """Return profile info for an existing profile."""
        metadata = self._read_metadata(platform, profile_id)
        p_log = get_profile_browser_logger(name="ProfileManager", profile_id=profile_id)
        p_log.debug(f"Retrieved profile [{profile_id}] for platform [{platform}]")
        return ProfileInfo.from_metadata(metadata)

    def is_profile_exists(self, platform: Platform, profile_id: str) -> bool:
        """Check whether a profile directory exists."""
        platform_dir = self.directory.get_platform_dir(platform)
        if not platform_dir.exists():
            return False
        profile_path = platform_dir / profile_id
        return profile_path.exists() and profile_path.is_dir()

    def list_profiles(
        self, platform: Optional[Platform] = None
    ) -> Dict[str, List[str]]:
        """
        List profiles.

        - If platform is provided → returns {platform: [profile_ids]}
        - If not provided → returns {platform1: [...], platform2: [...], ...}
        """
        results: Dict[str, List[str]] = {}

        if platform:
            platform_dir = self.directory.get_platform_dir(platform)
            if platform_dir.exists():
                results[platform] = [
                    p.name for p in platform_dir.iterdir() if p.is_dir()
                ]
        else:
            for plat in self.directory.platforms_dir.iterdir():
                if plat.is_dir():
                    results[plat.name] = [
                        profile.name for profile in plat.iterdir() if profile.is_dir()
                    ]

        self.log.debug(f"Listed profiles. Total platforms checked: {len(results)}")
        return results

    # ------------------------------------------------------------------
    # Encryption key management
    # ------------------------------------------------------------------

    def enable_encryption(self, platform: Platform, profile_id: str) -> None:
        """
        Generate a fresh AES-256 key for this profile, persist it to
        ``encryption.key``, and mark encryption as enabled in metadata.

        Raises:
            ValueError: If encryption is already enabled for this profile.

        Example::

            manager.enable_encryption(Platform.WHATSAPP, "my_profile")
            key = manager.get_key(Platform.WHATSAPP, "my_profile")
        """

        metadata = self._read_metadata(platform, profile_id)

        if metadata["encryption"].get("enabled"):
            raise ValueError(
                f"Encryption is already enabled for profile '{profile_id}'. "
                "Disable it first before re-enabling."
            )

        # Generate a random 32-byte key (no password derivation — the key file IS the secret)
        raw_key: bytes = KeyManager.generate_random_key()
        encoded_key: str = KeyManager.encode_key_for_storage(raw_key)

        # Write key file with strict permissions (owner read-only)
        key_file: Path = self.directory.get_key_file_path(platform, profile_id)
        key_file.write_text(encoded_key, encoding="utf-8")
        try:
            os.chmod(key_file, 0o600)  # -rw------- on Linux/macOS
        except OSError:
            pass  # Windows: chmod is a no-op, skip silently

        # Update metadata encryption block — NO key material stored here
        metadata["encryption"]["enabled"] = True
        metadata["encryption"]["created_at"] = datetime.now(timezone.utc).isoformat()
        self._write_metadata(platform, profile_id, metadata)
        self.log.info(
            f"Encryption enabled for profile : [{profile_id}] , platform : [{platform}] , stored at [{key_file}]"
        )

    def get_key(self, platform: Platform, profile_id: str) -> bytes:
        """
        Load and return the raw AES-256 key for this profile.
        Use this when resuming a session to get the key back for ``MessageDecryptor``.

        Raises:
            ValueError: If encryption is not enabled for this profile.
            FileNotFoundError: If the key file is missing (profile corruption).

        Example::

            key = manager.get_key(Platform.WHATSAPP, "my_profile")
            decryptor = MessageDecryptor(key)
            plaintext = decryptor.decrypt_message(nonce_bytes, cipher_bytes)
        """

        metadata = self._read_metadata(platform, profile_id)

        if not metadata["encryption"].get("enabled"):
            raise ValueError(
                f"Encryption is not enabled for profile '{profile_id}'. "
                "Call enable_encryption() first."
            )

        key_file: Path = self.directory.get_key_file_path(platform, profile_id)

        if not key_file.exists():
            raise FileNotFoundError(
                f"Encryption key file missing for profile '{profile_id}' "
                f"(expected: {key_file}). The profile may be corrupted."
            )

        encoded_key = key_file.read_text(encoding="utf-8").strip()

        p_log = get_profile_browser_logger(name="ProfileManager", profile_id=profile_id)
        p_log.debug(f"Encryption key retrieved for profile [{profile_id}]")

        return KeyManager.decode_key_from_storage(encoded_key)

    def is_encryption_enabled(self, platform: Platform, profile_id: str) -> bool:
        """Return True if encryption is currently enabled for this profile."""
        metadata = self._read_metadata(platform, profile_id)
        return bool(metadata["encryption"].get("enabled", False))

    def disable_encryption(self, platform: Platform, profile_id: str) -> None:
        """
        Disable encryption for this profile and wipe the key file.

        Warning:
            - This permanently deletes the encryption key.
            - Any messages already stored as ciphertext in the database will be irrecoverable.
            - Decrypt all messages *before* calling this if you need the plaintext.

        Raises:
            ValueError: If encryption is not enabled for this profile.
        """
        metadata = self._read_metadata(platform, profile_id)

        if not metadata["encryption"].get("enabled"):
            raise ValueError(f"Encryption is not enabled for profile '{profile_id}'.")

        # Securely remove the key file
        key_file: Path = self.directory.get_key_file_path(platform, profile_id)
        if key_file.exists():
            # Overwrite with zeros before unlinking to reduce forensic recoverability
            key_size = key_file.stat().st_size
            key_file.write_bytes(b"\x00" * key_size)
            key_file.unlink()

        # Reset metadata
        metadata["encryption"]["enabled"] = False
        metadata["encryption"]["created_at"] = None
        self._write_metadata(platform, profile_id, metadata)

        # Use profile-specific browser logger
        p_log = get_profile_browser_logger(name="ProfileManager", profile_id=profile_id)
        p_log.warning(
            f"Encryption disabled for profile [{profile_id}] & Key Destroyed."
        )

    # ------------------------------------------------------------------
    # Profile activation / deactivation
    # ------------------------------------------------------------------

    @staticmethod
    def is_pid_alive(pid: int) -> bool:
        """Checks PID if alive or not."""
        if not pid or pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        else:
            return True

    async def close_profile(self, profile: ProfileInfo, force: bool = False) -> None:
        """closes the profile
        :param profile: ProfileInfo
        :param force: Force close | Default = False
        """
        profile_id = profile.profile_id
        platform = profile.platform

        profile_dir = self.directory.get_profile_dir(platform, profile_id)
        metadata_file = profile_dir / "metadata.json"
        lock_file = profile_dir / ".lock"

        if not metadata_file.exists():
            raise ValueError("Profile metadata not found.")

        with open(metadata_file) as f:
            data = json.load(f)

        if not data["status"]["is_active"]:
            return

        pid = data["status"].get("last_active_pid")

        if pid:
            closed = await CamoufoxBrowser.close_browser_by_profile(profile_id)

            if not closed:
                if force and ProfileManager.is_pid_alive(pid):
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                elif ProfileManager.is_pid_alive(pid):
                    raise RuntimeError(
                        f"Browser process {pid} still running. Use force=True to terminate."
                    )

        data["status"]["is_active"] = False
        data["status"]["last_active_pid"] = None

        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=4)

        if lock_file.exists():
            lock_file.unlink()

        ProfileManager.__dec__()

        p_log = get_profile_browser_logger(name="ProfileManager", profile_id=profile_id)
        p_log.info(f"Profile closed successfully [{profile_id}]")

    def activate_profile(
        self, platform: Platform, profile_id: str, browser: CamoufoxBrowser
    ) -> None:
        """
        Activate a profile. Raises if already active with a live PID.
        Automatically forces headless=True when multiple profiles are running.
        """
        profile_dir = self.directory.get_profile_dir(platform, profile_id)

        if not profile_dir.exists():
            raise ValueError(
                f"Profile '{profile_id}' does not exist for platform '{platform}'."
            )

        metadata_file = profile_dir / "metadata.json"

        with open(metadata_file) as f:
            metadata = json.load(f)

        if not metadata.get("paths"):
            raise ValueError("Corrupted metadata file.")

        lock_file = profile_dir / ".lock"

        if metadata["status"]["is_active"]:
            pid = metadata["status"]["last_active_pid"]

            if pid and ProfileManager.is_pid_alive(pid):
                raise RuntimeError("Profile already active.")

            # Stale session cleanup
            metadata["status"]["is_active"] = False
            metadata["status"]["last_active_pid"] = None

            if lock_file.exists():
                lock_file.unlink()

        if ProfileManager.__p_count__() >= 1:
            browser.config.headless = True

        ProfileManager.__inc__()

        metadata["status"]["is_active"] = True
        metadata["status"]["last_active_pid"] = os.getpid()
        metadata["last_used"] = datetime.now(timezone.utc).isoformat()

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=4)

        lock_file.write_text(str(os.getpid()))

        p_log = get_profile_browser_logger(name="ProfileManager", profile_id=profile_id)
        p_log.info(f"Profile activated successfully [{profile_id}]")

    def delete_profile(self, profile: ProfileInfo, force: bool = False) -> None:
        """
        Completely delete a profile from the saved disk.
        To delete & remove access on your phone follow :
        1. Activate the profile.
        2. close the bot | profile .
        3. remove access to the latest active browser in "Linked Devices"
        :param profile: ProfileInfo
        :param force: Force delete | Default = False
        :return: None
        """
        platform = profile.platform
        profile_id = profile.profile_id

        profile_dir = self.directory.get_profile_dir(platform, profile_id)

        if not profile_dir.exists():
            raise ValueError(
                f"Profile '{profile_id}' does not exist for platform '{platform}'."
            )

        metadata_file = profile_dir / "metadata.json"

        with open(metadata_file) as f:
            metadata = json.load(f)

        if metadata["status"]["is_active"] and not force:
            raise ValueError(
                f"Cannot delete active profile [{profile_id}]. Deactivate first or use force=True."
            )

        self.log.debug(f"Deleting profile [{profile_id}] platform [{platform}]")

        shutil.rmtree(profile_dir)
        self.log.info(f"Profile deleted successfully [{profile_id}]")
