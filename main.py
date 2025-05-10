from sites import swri
from sites import umich
from sites import lanl
import os
import shutil
import logging

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

    all_jobs = []
    all_jobs.extend(lanl.fetch_jobs())
    all_jobs.extend(swri.fetch_jobs())
    all_jobs.extend(umich.fetch_jobs())

if __name__ == "__main__":
    run_all()
