import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger("osu")

KEYWORDS = ["software", "firmware", "embedded", "robotics", "autonomy"]
BASE_URL = "https://osu.wd1.myworkdayjobs.com/OSUCareers"


def fetch_jobs():
    jobs = []
    logger.info("OSU: Starting Selenium WebDriver")

    driver = webdriver.Chrome()

    try:
        logger.info(f"OSU: Navigating to {BASE_URL}")
        driver.get(BASE_URL)

        # Wait for the keyword search box to appear
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-automation-id='keywordSearchInput']"))
        )

        # Clear, enter search keyword, and submit
        keyword = "embedded"
        search_box.clear()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)

        # Wait for results to appear
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul[role='list']"))
        )
        time.sleep(2)

        while True:
            links = driver.find_elements(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")
            logger.info(f"OSU: Found {len(links)} job links on this page")

            for link in links:
                title = link.text.strip().lower()
                href = link.get_attribute("href")
                if any(keyword in title for keyword in KEYWORDS):
                    logger.info(f"OSU: Matched job - {title}")
                    jobs.append({"title": title, "url": href})

            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='next']")
                if "disabled" in next_button.get_attribute("class"):
                    logger.info("OSU: No more pages. Reached the end.")
                    break
                else:
                    logger.info("OSU: Moving to next page")
                    next_button.click()
                    WebDriverWait(driver, 15).until(
                        EC.staleness_of(links[0])  # Wait until new page loads
                    )
            except Exception:
                logger.info("OSU: No 'next' button found or failed to click. Ending pagination.")
                break

    except Exception as e:
        logger.error(f"OSU: Failed to fetch jobs - {e}")

    finally:
        driver.quit()

    return jobs


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = fetch_jobs()
    print(f"Found {len(results)} matching jobs")
    for job in results:
        print(job["title"], "->", job["url"])
