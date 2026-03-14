from __future__ import annotations

import argparse
import json
from pathlib import Path


def crawl_itviec(max_pages: int = 1) -> list[dict]:
    """Starter stub for ITViec crawling."""
    jobs = []
    for page in range(1, max_pages + 1):
        jobs.append(
            {
                "job_id": f"itviec-demo-{page}",
                "source": "ITViec",
                "job_title": "Sample Python Developer",
                "company_name": "Demo Company",
                "location": "Ho Chi Minh City",
                "company_type": "Product",
                "level": "Junior",
                "experience_years": 1,
                "salary_min": 15000000,
                "salary_max": 25000000,
                "salary_avg": 20000000,
                "salary_currency": "VND",
                "job_description": "Python, Django, REST API",
                "skills_extracted": ["Python", "Django", "REST API"],
                "posted_date": None,
                "job_url": "https://www.itviec.com/",
            }
        )
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Starter crawler for ITViec.")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("data/raw/itviec_jobs.json"))
    args = parser.parse_args()

    jobs = crawl_itviec(max_pages=args.pages)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(jobs, ensure_ascii=True, indent=2))
    print(f"Saved {len(jobs)} jobs to {args.output}")


if __name__ == "__main__":
    main()
