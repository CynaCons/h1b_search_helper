import os
import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def fetch_jobs():
    """Scrape Southwest Research Institute job postings."""

    # Keywords used to filter relevant job postings
    keywords = ["embedded", "software", "automotive"]

    # Set up the Selenium WebDriver (ensure the appropriate driver is installed)
    driver = webdriver.Chrome()  # or webdriver.Firefox(), etc.
    driver.get("https://resapp.swri.org/ResApp/Job_Search.aspx")

    jobs = []
    all_titles = []  # To store all job titles for logging

    try:
        # Click the 'Search' button
        search_button = driver.find_element(By.ID, "btnSearch")
        search_button.click()

        # Wait for the results page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "tblHistory"))
        )

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for row in soup.select("table#tblHistory tr")[1:]:
            columns = row.find_all("td")
            if not columns:
                continue
            title = columns[1].get_text(strip=True)
            link_tag = columns[1].find("a")
            link = link_tag["href"]
            all_titles.append(title)  # Add title to the list

            # Check if any keyword is in the title
            if any(
                keyword.lower() in title.lower()
                for keyword in keywords
            ):
                jobs.append({"title": title, "url": link})

    finally:
        driver.quit()

        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", "swri_jobs.yaml")
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump({"all_titles": all_titles, "jobs": jobs}, f, allow_unicode=True)

    return jobs
