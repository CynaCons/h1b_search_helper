import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Define the log format
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
        # Navigate directly to the job search page.  The previous root URL
        # https://careers.umich.edu/ performs a redirect that Selenium sometimes
        # fails to treat as secure which results in an error.  Loading the
        # dedicated search page avoids this issue.
        driver.get("https://careers.umich.edu/search-jobs")

        # Click the "Search" button to load all jobs without any filters.  This
        # button has the id "edit-submit-job-search" and must be clicked before
        # the results table is populated.
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "edit-submit-job-search"))
        )
        search_button.click()

        while True:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#block-system-main-block table.cols-5"))
            )
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.select_one("#block-system-main-block table.cols-5 tbody")
            rows = table.find_all("tr")

            for row in rows:
                title_cell = row.find("td", class_="views-field-title")
                if not title_cell:
                    continue
                link_tag = title_cell.find("a")
                if not link_tag:
                    continue

                title = link_tag.get_text(strip=True)
                url = "https://careers.umich.edu" + link_tag["href"]
                all_titles.append(title)

                if any(keyword in title.lower() for keyword in KEYWORDS):
                    jobs.append({"title": title, "url": url})
                    logger.info(f"UMICH: Match found -> {title}")

            # Try to find the next page button
            try:
                next_button_list = driver.find_elements(By.CSS_SELECTOR, "nav[role='navigation'] ul.js-pager__items li a[rel='next']")

                next_button_list[0].click()
            except:
                logger.info("UMICH: No more pages.")
                break

    except Exception as e:
        logger.error(f"UMICH: Error while fetching jobs - {e}")

    finally:
        driver.quit()

        # Save titles
        os.makedirs("output", exist_ok=True)
        with open("output/job_titles_umich.txt", "w", encoding="utf-8") as f:
            for title in all_titles:
                f.write(title + "\n")

        with open("output/job_results_umich.txt", "w", encoding="utf-8") as f:
            for job in jobs:
                f.write(f"{job['title']} -> {job['url']}\n")

    return jobs
