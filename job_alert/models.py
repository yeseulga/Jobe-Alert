from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class JobPosting:
    platform: str
    company: str
    title: str
    location: Optional[str]
    salary: Optional[str]
    size: Optional[str]
    deadline: Optional[str]
    rating: Optional[str]
    url: str
    description: Optional[str]
    published_at: Optional[datetime]


def job_id(job: JobPosting) -> str:
    # A stable identifier for deduplication: platform + url
    # URL is usually unique; we combine platform as a safety namespace
    return f"{job.platform}::{job.url.strip()}"
