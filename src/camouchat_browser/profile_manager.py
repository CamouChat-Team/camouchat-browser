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
from typing import List, Optional, Dict, Union

from camouchat_core import Platform, StorageType, KeyManager

from .browser_logger import logger, get_profile_browser_logger
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
        self,
        platform: Platform,
        profile_id: str,
        storage_type: StorageType = StorageType.SQLITE,
        database_url: Optional[str] = None,
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()

        db_path = self.directory.get_database_path(platform, profile_id)
        if not database_url:
            if storage_type == StorageType.SQLITE:
                database_url = f"sqlite+aiosqlite:///{db_path}"
            elif storage_type == StorageType.MYSQL:
                database_url = "mysql+aiomysql://user:pass@localhost/camouchat"
            elif storage_type == StorageType.POSTGRESQL:
                database_url = "postgresql+asyncpg://user:pass@localhost/camouchat"

        return {
            "profile_id": profile_id,
            "platform": platform,
            "version": "0.6",
            "created_at": now,
            "last_used": now,
            "database": {
                "type": storage_type,
                "url": database_url,
            },
            "paths": {
                "profile_dir": str(
                    self.directory.get_profile_dir(platform, profile_id)
                ),
                "fingerprint_file": "fingerprint.pkl",
                "cache_dir": "cache",
                "media_dir": "media",
                "media_images": "media/images",
                "media_videos": "media/videos",
                "media_voice": "media/voice",
                "database_file": "messages.db",
                "media_documents": "media/documents",
            },
            # The actual key lives in encryption.key — NOT here.
            "encryption": {
                "enabled": False,
                "algorithm": "AES-256-GCM",
                "key_file": "encryption.key",
                "created_at": None,  # set when enable_encryption() is called
            },
            "status": {
                "is_active": False,
                "last_active_pid": None,
                "lock_file": ".lock",
            },
        }

    def _read_metadata(self, platform: Platform, profile_id: str) -> dict:
        profile_dir = self.directory.get_profile_dir(platform, profile_id)
        metadata_file = profile_dir / "metadata.json"
        if not metadata_file.exists():
            raise ValueError(
                f"Profile metadata not found for '{profile_id}' on '{platform}'."
            )
        with open(metadata_file) as f:
            return json.load(f)

    def _write_metadata(self, platform: Platform, profile_id: str, data: dict) -> None:
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
        self,
        platform: Platform,
        profile_id: str,
        storage_type: StorageType = StorageType.SQLITE,
        database_url: Optional[str] = None,
    ) -> ProfileInfo:
        """
        Create a new profile; returns the existing one if already present.

        args :
        -platform : Platform must use from camouchat-core
        -profile_id : id/name of the profile to create
        -storage_type : type of storage must use from camouchat-core's StorageType , Default set to SQLITE
        -database_url : specific path to set url
                        Recommended to keep it default set , as it uses internally correct path to use according to Profile creation.

        :return - ProfileInfo object
        """
        profile_dir = self.directory.get_profile_dir(platform, profile_id)

        if profile_dir.exists():
            return self.get_profile(platform, profile_id)

        profile_dir.mkdir(parents=True, exist_ok=True)

        self.directory.get_cache_dir(platform, profile_id)
        self.directory.get_media_images_dir(platform, profile_id)
        self.directory.get_media_videos_dir(platform, profile_id)
        self.directory.get_media_voice_dir(platform, profile_id)
        self.directory.get_media_documents_dir(platform, profile_id)

        (profile_dir / "fingerprint.pkl").write_bytes(b"")

        metadata = self._generate_metadata(
            platform=platform,
            profile_id=profile_id,
            storage_type=storage_type,
            database_url=database_url,
        )
        self._write_metadata(platform, profile_id, metadata)

        # Use profile-specific browser logger
        p_log = get_profile_browser_logger(name="ProfileManager", profile_id=profile_id)
        p_log.info(
            f"Profile created with name [{profile_id}] & stored at [{profile_dir}]"
        )
        return ProfileInfo.from_metadata(metadata, self.directory)

    def get_profile(self, platform: Platform, profile_id: str) -> ProfileInfo:
        """Return profile info for an existing profile."""
        metadata = self._read_metadata(platform, profile_id)
        return ProfileInfo.from_metadata(metadata, self.directory)

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

        return results

    # ------------------------------------------------------------------
    # Encryption key management
    # ------------------------------------------------------------------

    def enable_encryption(self, platform: Platform, profile_id: str) -> bytes:
        """
        Generate a fresh AES-256 key for this profile, persist it to
        ``encryption.key``, and mark encryption as enabled in metadata.

        Returns the raw 32-byte key so the caller can hand it straight
        to ``MessageProcessor`` without ever having to re-read the file
        in the same session.

        Raises:
            ValueError: If encryption is already enabled for this profile.

        Example::

            key = manager.enable_encryption(Platform.WHATSAPP, "my_profile")
            processor = MessageProcessor(..., encryption_key=key)
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
        return raw_key

    def get_key(self, platform: Platform, profile_id: str) -> bytes:
        """
        Load and return the raw AES-256 key for this profile.

        Use this when resuming a session to get the key back for
        ``MessageProcessor`` or ``MessageDecryptor``.

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
        return KeyManager.decode_key_from_storage(encoded_key)

    def is_encryption_enabled(self, platform: Platform, profile_id: str) -> bool:
        """Return True if encryption is currently enabled for this profile."""
        metadata = self._read_metadata(platform, profile_id)
        return bool(metadata["encryption"].get("enabled", False))

    def disable_encryption(self, platform: Platform, profile_id: str) -> None:
        """
        Disable encryption for this profile and wipe the key file.

        .. warning::
            This permanently deletes the encryption key. Any messages already
            stored as ciphertext in the database will be irrecoverable.
            Decrypt all messages *before* calling this if you need the plaintext.

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

    async def close_profile(
        self, platform: Platform, profile_id: str, force: bool = False
    ) -> None:
        """closes the profile
        :param platform: Platform object
        :param profile_id: Profile ID
        :param force: Force close | Default = False
        """
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
            closed = await CamoufoxBrowser.close_browser_by_pid(pid)

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

    def activate_profile(
        self, platform: Platform, profile_id: str, browser_obj: CamoufoxBrowser
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
            browser_obj.config.headless = True

        ProfileManager.__inc__()

        metadata["status"]["is_active"] = True
        metadata["status"]["last_active_pid"] = os.getpid()
        metadata["last_used"] = datetime.now(timezone.utc).isoformat()

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=4)

        lock_file.write_text(str(os.getpid()))

    def delete_profile(
        self, platform: Platform, profile_id: str, force: bool = False
    ) -> None:
        """
        Completely delete a profile from the saved disk.
        To delete & remove access on your phone follow :
        1. Activate the profile.
        2. close the bot | profile .
        3. remove access to the latest active browser in "Linked Devices"
        :param platform: Platform object
        :param profile_id: profile ID
        :param force: Force delete | Default = False
        :return: None
        """
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
                f"Cannot delete active profile '{profile_id}'. Deactivate first or use force=True."
            )

        self.log.info("Deleting profile %s platform : %s", profile_id, platform)

        shutil.rmtree(profile_dir)
