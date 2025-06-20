import logging
import os
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

SEARCH_URL = (
    "https://ecsr.fa.us2.oraclecloud.com/"
    "hcmUI/CandidateExperience/en/sites/CX_1/jobs?mode=location"
)


def fetch_jobs():
    jobs = []
    all_titles = []
    driver = webdriver.Chrome()

    try:
        driver.get(SEARCH_URL)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.job-list-item__link"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        for link in soup.select("a.job-list-item__link"):
            url = link.get("href")
            title_elem = link.find_next("h3", class_="job-list-item__title")
            title = title_elem.get_text(strip=True) if title_elem else (
                link.get("aria-label") or link.get("title")
            )
            if not title or not url:
                continue
            all_titles.append(title)
            if any(keyword in title.lower() for keyword in KEYWORDS):
                jobs.append({"title": title, "url": url})
                logger.info(f"VANDERBILT_ISIS: Match found -> {title}")
    except Exception as e:
        logger.error(f"VANDERBILT_ISIS: Error while fetching jobs - {e}")
    finally:
        driver.quit()
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", "vanderbilt_isis_jobs.yaml")
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump({"all_titles": all_titles, "jobs": jobs}, f, allow_unicode=True)
        logger.info(f"VANDERBILT_ISIS: Job data written to {output_path}")

    return jobs


if __name__ == "__main__":
    logger.info("Starting VANDERBILT_ISIS job fetcher...")
    fetch_jobs()
