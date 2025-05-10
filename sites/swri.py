import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def fetch_jobs():
    # Define the list of keywords to search for
    keywords = ["embedded", "software", "automotive"]

    # Set up the Selenium WebDriver (ensure the appropriate driver is installed)
    driver = webdriver.Chrome()  # or webdriver.Firefox(), etc.
    driver.get("https://resapp.swri.org/ResApp/Job_Search.aspx")

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
        jobs = []
        job_titles = []  # To store all job titles for logging
        for row in soup.select("table#tblHistory tr")[1:]:
            columns = row.find_all("td")
            if not columns:
                continue
            title = columns[1].get_text(strip=True)
            link_tag = columns[1].find("a")
            link = link_tag["href"]
            job_desc = link_tag.get("job_desc", "").strip()  # Extract the job_desc attribute
            job_titles.append(title)  # Add title to the list

            # Check if any keyword is in the title or job description
            if any(keyword.lower() in title.lower() or keyword.lower() in job_desc.lower() for keyword in keywords):
                jobs.append({"title": title, "url": link, "description": job_desc})

        # Ensure the output directory exists
        output_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        os.makedirs(output_dir, exist_ok=True)

        # Write all job titles to a text file
        with open(os.path.join(output_dir, "job_titles_swri.txt"), "w", encoding="utf-8") as file:
            for job_title in job_titles:
                file.write(job_title + "\n")

        return jobs

    finally:
        driver.quit()
