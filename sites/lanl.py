import logging
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup



KEYWORDS = [
    "embedded", "firmware", "autosar", "real-time", "real time", "software",
    "bare metal", "bsp", "rtos", "low level", "low-level", "device driver"
]

logger = logging.getLogger("lanl")

def fetch_jobs():
    jobs = []
    all_titles = []
    driver = webdriver.Chrome()

    try:
        driver.get("https://lanl.jobs/search/searchjobs")
        
        # Click "Load more jobs" button until it's no longer found
        max_clicks = 50
        for i in range(max_clicks):
            try:
                load_more = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.jtable-page-number-next.ui-button.ui-state-default"))
                )
                # Hover over it
                actions = ActionChains(driver)
                actions.move_to_element(load_more).perform()
                load_more.click()
                logger.info(f"LANL: Clicked 'Load more jobs' ({i + 1}/{max_clicks})")
                time.sleep(0.5)  # wait for new content to load
            except:
                logger.info("LANL: No more 'Load more jobs' button visible.")
                break

        # Parse jobs once all loaded
        soup = BeautifulSoup(driver.page_source, "html.parser")
        table = soup.select_one("div#data table.jtable tbody")
        rows = table.find_all("tr") if table else []

        for row in rows:
            try:
                title_span = row.select_one("td.title-column span")
                title = title_span.get_text(strip=True) if title_span else None
                url = row.get("data-href")

                if not title or not url:
                    continue

                all_titles.append(title)

                if any(keyword in title.lower() for keyword in KEYWORDS):
                    jobs.append({"title": title, "url": url})
                    logger.info(f"LANL: Match found -> {title}")

            except Exception as e:
                logger.warning(f"LANL: Skipping a row due to parsing error: {e}")

    except Exception as e:
        logger.error(f"LANL: Error while fetching jobs - {e}")

    finally:
        driver.quit()

        os.makedirs("output", exist_ok=True)
        with open("output/job_titles_lanl.txt", "w", encoding="utf-8") as f:
            for title in all_titles:
                f.write(title + "\n")

        with open("output/job_results_lanl.txt", "w", encoding="utf-8") as f:
            for job in jobs:
                f.write(f"{job['title']} -> {job['url']}\n")

    return jobs
