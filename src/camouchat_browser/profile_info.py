from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

from camouchat_core import Platform


@dataclass
class ProfileInfo:
    """
    Represents metadata and resolved filesystem paths for a CamouChat profile.

    This class acts as a structured container combining:
    - Raw metadata (loaded from profile storage)
    - Derived filesystem paths (resolved via directory manager)
    - Runtime state (active status, process tracking)

    Attributes:
        profile_id: Unique identifier for the profile.
        platform: Target platform (e.g., WhatsApp).
        version: Profile schema/version.
        created_at: Profile creation timestamp.
        last_used: Last usage timestamp.

        profile_dir: Root directory of the profile.
        fingerprint_path: Path to stored browser fingerprint.
        cache_dir: Browser/cache directory.
        media_dir: Root media directory.

        media_images_dir: Images storage path.
        media_videos_dir: Videos storage path.
        media_voice_dir: Voice notes storage path.
        media_documents_dir: Documents storage path.

        database_path: Local database file path.
        database_url: SQLAlchemy-compatible DB URL.

        is_active: Whether profile is currently active.
        last_active_pid: Last known process ID using this profile.

        encryption: Encryption-related metadata/config.
    """

    # --- Identity ---
    profile_id: str
    platform: Platform
    version: str
    created_at: str
    last_used: str

    # --- Paths ---
    profile_dir: Path
    fingerprint_path: Path
    cache_dir: Path
    media_dir: Path
    media_images_dir: Path
    media_videos_dir: Path
    media_voice_dir: Path
    media_documents_dir: Path

    # db credentials.
    db_type: Optional[str]
    database_path: Optional[Path]
    username: Optional[str]
    password: Optional[str]
    host: Optional[str]
    port: Optional[int]
    database_name: Optional[str]

    # --- Runtime state ---
    is_active: bool
    last_active_pid: Optional[int]

    # --- Security ---
    encryption: Dict[str, Any]

    @classmethod
    def from_metadata(cls, metadata: Dict[str, Any]) -> "ProfileInfo":
        """
        Construct a ProfileInfo instance from raw metadata and a directory manager.

        This method:
        - Extracts required fields from metadata
        - Resolves all filesystem paths using `directory`
        - Applies backward compatibility for database configuration

        Args:
            metadata: Raw metadata dictionary (loaded from profile file).

        Returns:
            ProfileInfo: Fully initialized profile representation.
        """

        status = metadata.get("status", {})

        return cls(
            # Identity
            profile_id=metadata["profile_id"],
            platform=metadata["platform"],
            version=metadata["version"],
            created_at=metadata["created_at"],
            last_used=metadata["last_used"],
            # Paths
            profile_dir=Path(metadata["paths"]["profile_dir"]),
            fingerprint_path=Path(metadata["paths"]["fingerprint_file"]),
            cache_dir=Path(metadata["paths"]["cache_dir"]),
            media_dir=Path(metadata["paths"]["media_dir"]),
            media_images_dir=Path(metadata["paths"]["media_images"]),
            media_videos_dir=Path(metadata["paths"]["media_videos"]),
            media_voice_dir=Path(metadata["paths"]["media_voice"]),
            media_documents_dir=Path(metadata["paths"]["media_documents"]),
            # database
            database_path=Path(metadata["database"]["database_path"]),
            db_type=metadata["database"]["storage_type"],
            username=metadata["database"]["username"],
            password=metadata["database"]["password"],
            host=metadata["database"]["host"],
            port=metadata["database"]["port"],
            database_name=metadata["database"]["database_name"],
            # Runtime
            is_active=status.get("is_active", False),
            last_active_pid=status.get("last_active_pid"),
            # Security
            encryption=metadata["encryption"],
        )

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "platform": self.platform,
            "version": self.version,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "profile_dir": self.profile_dir,
            "fingerprint_path": self.fingerprint_path,
            "cache_dir": self.cache_dir,
            "media_dir": self.media_dir,
            "media_images_dir": self.media_images_dir,
            "media_videos_dir": self.media_videos_dir,
            "media_voice_dir": self.media_voice_dir,
            "media_documents_dir": self.media_documents_dir,
            "database_path": self.database_path,
            "db_type": self.db_type,
            "username": self.username,
            "password": self.password,
            "host": self.host,
            "port": self.port,
            "database_name": self.database_name,
            "is_active": self.is_active,
            "last_active_pid": self.last_active_pid,
            "encryption": self.encryption,
        }

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return f"ProfileInfo({self.to_dict()})"
