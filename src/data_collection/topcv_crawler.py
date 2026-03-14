import os
import csv
import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://www.topcv.vn/tim-viec-lam-software-engineering-cr257cb258?page="

headers = {
    "User-Agent": "Mozilla/5.0"
}


def clean_salary(text):

    if not text:
        return None, None, None

    text = text.lower().replace(",", "").strip()

    nums = re.findall(r"\d+", text)

    if not nums:
        return None, None, None

    nums = [int(n) for n in nums]

    if "usd" in text or "$" in text:
        currency = "USD"
        multiplier = 1
    else:
        currency = "VND"
        multiplier = 1000000

    if len(nums) == 1:
        salary_min = nums[0] * multiplier
        salary_max = nums[0] * multiplier
    else:
        salary_min = nums[0] * multiplier
        salary_max = nums[1] * multiplier

    return salary_min, salary_max, currency


def parse_experience(text):

    if not text:
        return None

    nums = re.findall(r"\d+", text)

    if nums:
        return int(nums[0])

    return None


def crawl_topcv(pages=10):

    dataset = []

    for page in range(1, pages + 1):

        print("Crawling page", page)

        url = BASE_URL + str(page)

        r = requests.get(url, headers=headers)

        soup = BeautifulSoup(r.text, "html.parser")

        jobs = soup.select(".job-item-search-result")

        for job in jobs:

            try:

                # ===== job title (fix Lì xì)
                title_tag = job.select_one("h3.title a span")

                if not title_tag:
                    continue

                job_title = title_tag.text.strip()

                # ===== company
                company_tag = job.select_one(".company-name")
                company_name = company_tag.text.strip() if company_tag else ""

                # ===== salary
                salary_tag = job.select_one(".title-salary")
                salary_text = salary_tag.text.strip() if salary_tag else ""

                salary_min, salary_max, currency = clean_salary(salary_text)

                # ===== location
                location_tag = job.select_one(".city-text")
                location = location_tag.text.strip() if location_tag else ""

                # ===== experience
                exp_tag = job.select_one(".exp span")
                exp_text = exp_tag.text.strip() if exp_tag else ""

                experience_years = parse_experience(exp_text)

                # ===== skills
                skill_tags = job.select(".item-tag")

                skills = []

                for s in skill_tags:

                    skill = s.text.strip().lower()

                    if "kinh nghiệm" in skill:
                        continue

                    if "đại học" in skill:
                        continue

                    skills.append(skill)

                tech_stack = ", ".join(skills)

                dataset.append({

                    "job_title": job_title,
                    "tech_stack": tech_stack,
                    "experience_years": experience_years,
                    "location": location,
                    "company_name": company_name,
                    "remote_option": "onsite",
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "currency": currency

                })

                print("✔", job_title)

            except:
                continue

        time.sleep(2)

    return dataset


def save_csv(data):

    if not data:
        print("No data collected")
        return

    keys = data[0].keys()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"topcv_jobs_{timestamp}.csv"

    # data/raw cùng cấp với src (src/data_collection -> src -> project_root -> data/raw)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(f, fieldnames=keys)

        writer.writeheader()

        writer.writerows(data)


if __name__ == "__main__":

    jobs = crawl_topcv(20)

    save_csv(jobs)

    print("Total jobs:", len(jobs))
