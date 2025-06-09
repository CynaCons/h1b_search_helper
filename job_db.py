import os
import yaml
from typing import Dict, List

DB_PATH = os.path.join(os.path.dirname(__file__), "jobs_db.yaml")


def load_db() -> Dict[str, List[dict]]:
    """Load the database from disk."""
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_db(db: Dict[str, List[dict]]) -> None:
    """Persist the database to disk."""
    with open(DB_PATH, "w", encoding="utf-8") as f:
        yaml.dump(db, f, allow_unicode=True)


def add_jobs(site: str, jobs: List[dict], db: Dict[str, List[dict]]) -> List[dict]:
    """Add jobs for a site to the database and return the newly added ones."""
    existing = {job["url"] for job in db.get(site, []) if "url" in job}
    new_jobs = [job for job in jobs if job.get("url") not in existing]
    if new_jobs:
        db.setdefault(site, []).extend(new_jobs)
    return new_jobs
