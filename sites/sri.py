# Fix for removing 'Title' prefix from job titles in SRI fetcher
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

KEYWORDS = [
    "embedded", "firmware", "autosar", "real-time", "real time", "software",
    "bare metal", "bsp", "rtos", "low level", "low-level", "device driver"
]

logger = logging.getLogger(__name__)


def fetch_jobs():
    jobs = []
    all_titles = []
    driver = webdriver.Chrome()

    try:
        driver.get("https://careers-sri.icims.com/jobs/search?ss=1&searchRelation=keyword_all")

        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "icims_content_iframe"))
        )

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "iCIMS_JobsTable"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("div.container-fluid.iCIMS_JobsTable div.row")

        for row in rows:
            try:
                title_tag = row.select_one("a")
                title = title_tag.get_text(strip=True) if title_tag else None
                url = title_tag["href"] if title_tag else None

                if not title or not url:
                    continue

                # Remove 'Title' prefix if it exists
                if title.lower().startswith("title"):
                    title = title[5:].strip()

                all_titles.append(title)

                if any(keyword in title.lower() for keyword in KEYWORDS):
                    jobs.append({"title": title, "url": url})
                    logger.info(f"SRI: Match found -> {title}")

            except Exception as e:
                logger.warning(f"SRI: Skipping row due to error: {e}")

    except Exception as e:
        logger.error(f"SRI: Error while fetching jobs - {e}")

    finally:
        driver.quit()

        os.makedirs("output", exist_ok=True)
        with open("output/job_titles_sri.txt", "w", encoding="utf-8") as f:
            for title in all_titles:
                f.write(title + "\n")

        with open("output/job_results_sri.txt", "w", encoding="utf-8") as f:
            for job in jobs:
                f.write(f"{job['title']} -> {job['url']}\n")

    return jobs
