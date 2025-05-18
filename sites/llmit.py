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
        driver.get("https://careers.ll.mit.edu/search")

        # Wait for the search results table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchresults"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.select_one("table#searchresults tbody")
        rows = table.find_all("tr", class_="data-row") if table else []

        for row in rows:
            try:
                title_tag = row.select_one("td.colTitle a.jobTitle-link")
                title = title_tag.get_text(strip=True) if title_tag else None
                url = "https://careers.ll.mit.edu" + title_tag["href"] if title_tag else None

                if not title or not url:
                    continue

                all_titles.append(title)

                if any(keyword in title.lower() for keyword in KEYWORDS):
                    jobs.append({"title": title, "url": url})
                    logger.info(f"LLMIT: Match found -> {title}")

            except Exception as e:
                logger.warning(f"LLMIT: Skipping row due to error: {e}")

    except Exception as e:
        logger.error(f"LLMIT: Error while fetching jobs - {e}")

    finally:
        driver.quit()

        os.makedirs("output", exist_ok=True)
        with open("output/job_titles_llmit.txt", "w", encoding="utf-8") as f:
            for title in all_titles:
                f.write(title + "\n")

        with open("output/job_results_llmit.txt", "w", encoding="utf-8") as f:
            for job in jobs:
                f.write(f"{job['title']} -> {job['url']}\n")

    return jobs
