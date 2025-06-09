# h1b_search_helper
Application to search and report on Job Opportunities in H1B CapExempt Research Institutions

# Dependencies
pip install requests beautifulsoup4 lxml plyer selenium pyyaml

# Execution
python main.py

## Persistent Job Database
Each run updates `jobs_db.yaml` with all discovered jobs. When new jobs are found
during a run they are logged to the console. This makes it easy to see which
postings you haven't reviewed yet.

The output for each job fetcher is now written to `output/<site>_jobs.yaml`. Each
YAML file contains two lists:

```yaml
all_titles:
  - Job Title 1
  - Job Title 2
jobs:
  - title: Job Title 1
    url: https://example.com/job1
```

All fetchers share this format so the results can be easily processed.
