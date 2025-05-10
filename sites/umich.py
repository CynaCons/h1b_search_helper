import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

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
        driver.get("https://careers.umich.edu/")

        # Custom behavior per fetcher
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "edit-submit-job-search" if "umich" == "umich" else "ctl00_ContentPlaceHolder1_btnSearch"))
        )
        search_button.click()

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#block-system-main-block table.cols-5" if "umich" == "umich" else "table#ctl00_ContentPlaceHolder1_gvJobSearchResults"))
        )

        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.select_one("#block-system-main-block table.cols-5 tbody" if "umich" == "umich" else "table#ctl00_ContentPlaceHolder1_gvJobSearchResults tbody")
        rows = table.find_all("tr")

        for row in rows:
            title_cell = row.find("td", class_="views-field-title") if "umich" == "umich" else row.find_all("td")[0]
            if not title_cell:
                continue
            link_tag = title_cell.find("a")
            if not link_tag:
                continue
            title = link_tag.get_text(strip=True)
            all_titles.append(title)
            url = "https://careers.umich.edu" + link_tag["href"] if "umich" == "umich" else "https://resapp.swri.org" + link_tag["href"]

            if any(keyword in title.lower() for keyword in KEYWORDS):
                jobs.append({"title": title, "url": url})
                logger.info(f"UMICH: Match found -> {title}")

    except Exception as e:
        logger.error(f"UMICH: Error while fetching jobs - {e}")

    finally:
        driver.quit()

        # Write all found job titles
        with open(f"output/job_titles_umich.txt", "w", encoding="utf-8") as f:
            for title in all_titles:
                f.write(title + "\n")

        # Write matching job results
        with open(f"output/job_results_umich.txt", "w", encoding="utf-8") as f:
            for job in jobs:
                f.write(f"{job['title']} -> {job['url']}\n")

    return jobs
