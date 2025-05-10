from sites import swri
from utils.notifier import notify
import os
import shutil

def run_all():
    # Ensure the output directory is deleted at the start of each run
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)  # Remove the directory and its contents

    # Recreate the output directory
    os.makedirs(output_dir, exist_ok=True)

    all_jobs = []
    all_jobs.extend(swri.fetch_jobs())

    # File to store the job details
    output_file = os.path.join(output_dir, "job_results.txt")

    with open(output_file, "w", encoding="utf-8") as file:
        for job in all_jobs:
            job_details = (
                f"Title: {job['title']}\n"
                f"URL: {job['url']}\n"
                f"Description: {job['description']}\n"
            )
            print(job_details)  # Print to console
            file.write(job_details + "\n")  # Write to file
            # notify(job["title"], job["url"])  # Uncomment if notifications are needed

if __name__ == "__main__":
    run_all()
