from __future__ import annotations

import argparse
import json
from pathlib import Path


def crawl_topcv(max_pages: int = 1) -> list[dict]:
    """Starter stub for TopCV crawling."""
    jobs = []
    for page in range(1, max_pages + 1):
        jobs.append(
            {
                "job_id": f"topcv-demo-{page}",
                "source": "TopCV",
                "job_title": "Sample Java Developer",
                "company_name": "Demo Company",
                "location": "Ha Noi",
                "company_type": "Outsource",
                "level": "Fresher",
                "experience_years": 0,
                "salary_min": 12000000,
                "salary_max": 18000000,
                "salary_avg": 15000000,
                "salary_currency": "VND",
                "job_description": "Java, Spring Boot, SQL",
                "skills_extracted": ["Java", "Spring Boot", "SQL"],
                "posted_date": None,
                "job_url": "https://www.topcv.vn/",
            }
        )
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Starter crawler for TopCV.")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("data/raw/topcv_jobs.json"))
    args = parser.parse_args()

    jobs = crawl_topcv(max_pages=args.pages)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(jobs, ensure_ascii=True, indent=2))
    print(f"Saved {len(jobs)} jobs to {args.output}")


if __name__ == "__main__":
    main()
