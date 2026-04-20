from pathlib import Path

from platformdirs import PlatformDirs
from typing import Optional
from .browser_logger import get_profile_browser_logger, logger


class DirectoryManager:
    """
    Orchestrates application data and profile directory structures.

    Resolves OS-specific paths for root, cache, and platform directories,
    ensuring consistent storage across Linux, macOS, and Windows.
    """

    def __init__(self):
        """Initialize DirectoryManager with an application name."""
        self.dirs = PlatformDirs(appname="CamouChat", appauthor="BITS-Rohit")

        self.root_dir = Path(self.dirs.user_data_dir)
        self.cache_dir = Path(self.dirs.user_cache_dir)
        self.log_dir = Path(self.dirs.user_log_dir)

        self.platforms_dir = self.root_dir / "platforms"

        self._ensure_base_dirs()

    def _ensure_base_dirs(self):
        """Ensure that base directories (root, cache, logs, platforms) exist."""
        for d in [self.root_dir, self.cache_dir, self.log_dir, self.platforms_dir]:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Directory created: {d}")

    def setup_profile_directories(self, platform: str, profile_id: str) -> None:
        """Creates the entire directory structure for a profile at once."""
        self.get_platform_dir(platform).mkdir(parents=True, exist_ok=True)
        self.get_profile_dir(platform, profile_id).mkdir(parents=True, exist_ok=True)
        self.get_cache_dir(platform, profile_id).mkdir(parents=True, exist_ok=True)
        self.get_backup_dir(platform, profile_id).mkdir(parents=True, exist_ok=True)
        self.get_media_dir(platform, profile_id).mkdir(parents=True, exist_ok=True)
        self.get_media_images_dir(platform, profile_id).mkdir(
            parents=True, exist_ok=True
        )
        self.get_media_videos_dir(platform, profile_id).mkdir(
            parents=True, exist_ok=True
        )
        self.get_media_voice_dir(platform, profile_id).mkdir(
            parents=True, exist_ok=True
        )
        self.get_media_documents_dir(platform, profile_id).mkdir(
            parents=True, exist_ok=True
        )

        self.get_fingerprint_file_path(platform, profile_id).touch(exist_ok=True)
        self.get_key_file_path(platform, profile_id).touch(exist_ok=True)
        p_log = get_profile_browser_logger(
            name="DirectoryManager", profile_id=profile_id
        )
        p_log.info(
            f"Initialized directory structure for profile '{profile_id}' on platform '{platform}'"
        )

    def get_platform_dir(self, platform: str) -> Path:
        """Returns the directory for a specific platform."""
        return self.platforms_dir / platform.lower()

    def get_profile_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the base directory for a specific profile on a platform."""
        return self.get_platform_dir(platform) / profile_id

    def get_database_path(
        self, platform: str, profile_id: str, name: Optional[str] = None
    ) -> Path:
        """Returns the path to the database file for a profile.
        Name defaults to None — caller (e.g. SQLAlchemy storage) sets the filename.
        """
        path = self.get_profile_dir(platform, profile_id) / (name or "messages.db")
        path.touch(exist_ok=True)
        return

    def get_fingerprint_file_path(self, platform: str, profile_id: str) -> Path:
        """Returns the path to the fingerprint file for a profile."""
        return self.get_profile_dir(platform, profile_id) / "fingerprint.pkl"

    def get_key_file_path(self, platform: str, profile_id: str) -> Path:
        """
        Returns the path to the encryption key file for a profile.

        The key file is separate from metadata.json intentionally — metadata.json
        is a general-purpose readable file. The key file is a dedicated secret
        that only ProfileManager touches when encryption is enabled.

        File format: raw base64-encoded 32-byte AES-256 key (single line, no newline).
        """
        return self.get_profile_dir(platform, profile_id) / "encryption.key"

    def get_error_trace_file(self) -> Path:
        """Returns the path to the global ErrorTrace log file."""
        return self.cache_dir / "ErrorTrace.log"

    def get_browser_log_file(self) -> Path:
        """Returns the path to the dedicated browser log file."""
        return self.cache_dir / "browser.log"

    # ----------------------------
    # Profile Subdirectories
    # ----------------------------

    def get_cache_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the cache directory for a specific profile."""
        return self.get_profile_dir(platform, profile_id) / "cache"

    def get_backup_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the backup directory for a specific profile."""
        return self.get_profile_dir(platform, profile_id) / "backups"

    def get_media_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the root media directory for a specific profile."""
        return self.get_profile_dir(platform, profile_id) / "media"

    def get_media_images_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the images media directory for a specific profile."""
        return self.get_media_dir(platform, profile_id) / "images"

    def get_media_videos_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the videos media directory for a specific profile."""
        return self.get_media_dir(platform, profile_id) / "videos"

    def get_media_voice_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the voice media directory for a specific profile."""
        return self.get_media_dir(platform, profile_id) / "voice"

    def get_media_documents_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the documents media directory for a specific profile."""
        return self.get_media_dir(platform, profile_id) / "documents"

    # ----------------------------
    # Global paths
    # ----------------------------

    def get_cache_root(self) -> Path:
        """Returns the root cache directory."""
        return self.cache_dir

    def get_log_root(self) -> Path:
        """Returns the root log directory."""
        return self.log_dir
