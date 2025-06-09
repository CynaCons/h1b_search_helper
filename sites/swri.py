import os
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
            job_desc = link_tag.get("job_desc", "").strip()  # Extract the job_desc attribute
            all_titles.append(title)  # Add title to the list

            # Check if any keyword is in the title or job description
            if any(
                keyword.lower() in title.lower() or keyword.lower() in job_desc.lower()
                for keyword in keywords
            ):
                jobs.append({"title": title, "url": link, "description": job_desc})

    finally:
        driver.quit()

        # Ensure the output directory exists before writing
        os.makedirs("output", exist_ok=True)

        # Write all found job titles
        with open("output/job_titles_swri.txt", "w", encoding="utf-8") as f:
            for title in all_titles:
                f.write(title + "\n")

        # Write matching job results
        with open("output/job_results_swri.txt", "w", encoding="utf-8") as f:
            for job in jobs:
                job_details = (
                    f"Title: {job['title']}\n"
                    f"URL: {job['url']}\n"
                    f"Description: {job['description']}\n"
                )
                f.write(job_details + "\n")  # Write to file

    return jobs
