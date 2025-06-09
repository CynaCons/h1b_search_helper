from sites import swri
from sites import umich
from sites import lanl
from sites import sri
from sites import llmit
import os
import shutil
import logging
import job_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def run_all():
    # Ensure the output directory is deleted at the start of each run
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)  # Remove the directory and its contents

    # Recreate the output directory
    os.makedirs(output_dir, exist_ok=True)

    db = job_db.load_db()

    sites = [
        (lanl, "lanl"),
        (sri, "sri"),
        (llmit, "llmit"),
        (swri, "swri"),
        (umich, "umich"),
    ]

    all_jobs = []
    for module, name in sites:
        jobs = module.fetch_jobs()
        new_jobs = job_db.add_jobs(name, jobs, db)
        if new_jobs:
            logging.info(f"New jobs for {name}:")
            for job in new_jobs:
                logging.info(f"  {job['title']} | {job['url']}")
        all_jobs.extend(jobs)

    job_db.save_db(db)

if __name__ == "__main__":
    run_all()
