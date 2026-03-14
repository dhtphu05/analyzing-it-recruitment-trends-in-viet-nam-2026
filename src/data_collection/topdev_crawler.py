from __future__ import annotations

import argparse
import json
from pathlib import Path


def crawl_topdev(max_pages: int = 1) -> list[dict]:
    """Starter stub for TopDev crawling."""
    jobs = []
    for page in range(1, max_pages + 1):
        jobs.append(
            {
                "job_id": f"topdev-demo-{page}",
                "source": "TopDev",
                "job_title": "Sample Frontend Developer",
                "company_name": "Demo Company",
                "location": "Da Nang",
                "company_type": "Global",
                "level": "Senior",
                "experience_years": 4,
                "salary_min": 25000000,
                "salary_max": 40000000,
                "salary_avg": 32500000,
                "salary_currency": "VND",
                "job_description": "ReactJS, TypeScript, HTML, CSS",
                "skills_extracted": ["ReactJS", "TypeScript", "HTML", "CSS"],
                "posted_date": None,
                "job_url": "https://topdev.vn/",
            }
        )
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Starter crawler for TopDev.")
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("data/raw/topdev_jobs.json"))
    args = parser.parse_args()

    jobs = crawl_topdev(max_pages=args.pages)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(jobs, ensure_ascii=True, indent=2))
    print(f"Saved {len(jobs)} jobs to {args.output}")


if __name__ == "__main__":
    main()
