import logging
import os
import yaml
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

KEYWORDS = [
    "embedded", "firmware", "autosar", "real-time", "real time", "software",
    "bare metal", "bsp", "rtos", "low level", "low-level", "device driver"
]

logger = logging.getLogger(__name__)


def fetch_jobs():
    """Fetch job postings from Ohio State University's Workday feed."""
    url = "https://osu.wd1.myworkdayjobs.com/wday/cxs/osu/OSUCareers/jobs"
    headers = {"Content-Type": "application/json"}

    jobs = []
    all_titles = []

    offset = 0
    limit = 50
    total = None

    while total is None or offset < total:
        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": "",
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"OSU: Error fetching jobs at offset {offset}: {e}")
            break

        data = resp.json()
        total = data.get("total", 0)
        postings = data.get("jobPostings", [])

        for post in postings:
            title = post.get("title", "").strip()
            ext_path = post.get("externalPath")
            if not title or not ext_path:
                continue

            if not ext_path.startswith("http"):
                job_url = f"https://osu.wd1.myworkdayjobs.com/en-US/OSUCareers{ext_path}"
            else:
                job_url = ext_path

            all_titles.append(title)

            if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                jobs.append({"title": title, "url": job_url})
                logger.info(f"OSU: Match found -> {title}")

        offset += limit

    os.makedirs("output", exist_ok=True)
    output_path = os.path.join("output", "osu_jobs.yaml")
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump({"all_titles": all_titles, "jobs": jobs}, f, allow_unicode=True)
    logger.info(f"OSU: Job data written to {output_path}")

    return jobs
