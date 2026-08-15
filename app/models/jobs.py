"""Data model for tracking VCFDT download jobs.

This module defines a lightweight job record structure. In the current
single-container design, job state lives in-memory in VCFDTService.
These classes provide a typed structure for serialization (e.g. JSON
responses, future database persistence) and make it easier to swap
in a persistent backend later (SQLite, Redis, PostgreSQL) without
rewriting the route layer.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class JobRecord:
    """Represents a single VCFDT download job."""

    job_id: str
    command: str
    started_at: str
    status: str = "running"  # running | completed | failed | terminated
    pid: Optional[int] = None
    log_file: Optional[str] = None
    finished_at: Optional[str] = None
    returncode: Optional[int] = None

    def to_dict(self) -> dict:
        """Serialize to a dictionary for JSON responses."""
        d = asdict(self)
        # Don't expose the log file path externally
        d.pop("log_file", None)
        return d

    def is_finished(self) -> bool:
        return self.status in ("completed", "failed", "terminated")

    def is_running(self) -> bool:
        return self.status == "running"


@dataclass
class DepotComponent:
    """Represents a scanned component directory in the depot."""

    name: str
    size_bytes: int = 0
    file_count: int = 0

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 ** 3)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "size_bytes": self.size_bytes,
            "size_gb": round(self.size_gb, 2),
            "file_count": self.file_count,
        }


def utcnow_iso() -> str:
    """Helper to return an ISO 8601 timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()