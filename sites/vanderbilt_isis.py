import logging
import os
import yaml
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

KEYWORDS = [
    "embedded", "firmware", "autosar", "real-time", "real time", "software",
    "bare metal", "bsp", "rtos", "low level", "low-level", "device driver"
]

logger = logging.getLogger("VANDERBILT_ISIS")

SEARCH_URL = (
    "https://ecsr.fa.us2.oraclecloud.com/"
    "hcmUI/CandidateExperience/en/sites/CX_1/jobs?mode=location"
)


def fetch_jobs():
    jobs = []
    all_titles = []
    driver = webdriver.Chrome()

    try:
        logger.info("Navigating to search page")
        driver.get(SEARCH_URL)

        # Wait for search input and enter keyword
        search_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-qa='searchKeywordsInput']"))
        )
        search_input.clear()
        search_input.send_keys("software")

        # Click search button
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-qa='searchStartBtn']"))
        )
        search_button.click()

        # Wait for job result list to appear
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-list__list li[data-qa='searchResultItem']"))
        )

        # Scroll to bottom until no new jobs are loaded
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            logger.info("Scrolling to bottom to load more jobs...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info("Reached bottom of the page")
                break
            last_height = new_height

        entries = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-list__list li[data-qa='searchResultItem']")
        logger.info(f"Found {len(entries)} job entries on page")

        for entry in entries:
            try:
                title_elem = entry.find_element(By.CSS_SELECTOR, ".job-tile__title")
                title = title_elem.text.strip()
                link_elem = entry.find_element(By.CSS_SELECTOR, "a.job-list-item__link")
                url = link_elem.get_attribute("href")

                if not title or not url:
                    continue
                all_titles.append(title)

                if any(keyword in title.lower() for keyword in KEYWORDS):
                    jobs.append({"title": title, "url": url})
                    logger.info(f"Match found -> {title}")
            except Exception as e:
                logger.warning(f"Could not parse job entry: {e}")

    except Exception as e:
        logger.error(f"Error while fetching jobs - {e}")

    finally:
        driver.quit()
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", "vanderbilt_isis_jobs.yaml")
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump({"all_titles": all_titles, "jobs": jobs}, f, allow_unicode=True)
        logger.info(f"Job data written to {output_path}")

    return jobs


if __name__ == "__main__":
    logger.info("Starting VANDERBILT_ISIS job fetcher...")
    fetch_jobs()
