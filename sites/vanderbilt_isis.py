import logging
import os
import yaml
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

KEYWORDS = [
    "embedded", "firmware", "autosar", "real-time", "real time", "software",
    "bare metal", "bsp", "rtos", "low level", "low-level", "device driver"
]

logger = logging.getLogger(__name__)

FEED_URL = (
    "https://www.vanderbilt.edu/work-at-vanderbilt/feed/?post_type=job&"
    "s=Institute+for+Software+Integrated+Systems"
)


def fetch_jobs():
    jobs = []
    all_titles = []

    try:
        response = requests.get(FEED_URL, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "xml")
        for item in soup.find_all("item"):
            try:
                title = item.title.get_text(strip=True)
                link = item.link.get_text(strip=True)

                if not title or not link:
                    continue

                all_titles.append(title)

                if any(keyword in title.lower() for keyword in KEYWORDS):
                    jobs.append({"title": title, "url": link})
                    logger.info(f"VANDERBILT_ISIS: Match found -> {title}")

            except Exception as e:
                logger.warning(f"VANDERBILT_ISIS: Skipping item due to error: {e}")

    except Exception as e:
        logger.error(f"VANDERBILT_ISIS: Error while fetching jobs - {e}")

    finally:
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", "vanderbilt_isis_jobs.yaml")
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump({"all_titles": all_titles, "jobs": jobs}, f, allow_unicode=True)
        logger.info(f"VANDERBILT_ISIS: Job data written to {output_path}")

    return jobs


if __name__ == "__main__":
    logger.info("Starting VANDERBILT_ISIS job fetcher...")
    fetched_jobs = fetch_jobs()
    if fetched_jobs:
        logger.info(f"Successfully fetched {len(fetched_jobs)} jobs.")
    elif fetched_jobs == []:
        logger.info(
            "VANDERBILT_ISIS job fetcher ran successfully but found 0 relevant jobs or 0 total jobs."
        )
    else:
        logger.warning(
            "VANDERBILT_ISIS job fetcher did not return a valid job list, likely encountered an issue."
        )

