import re
import time
import csv
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup


BASE_URL = "https://itviec.com/it-jobs?page="


# =============================
# Create driver
# =============================

def create_driver():

    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


# =============================
# Salary parser
# =============================

def clean_salary(text):

    if not text:
        return None, None, None

    text = text.lower().replace(",", "")

    if "love" in text:
        return None, None, None

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


# =============================
# Detect remote / onsite
# =============================

def detect_remote(text):

    text = text.lower()

    if "remote" in text:
        return "remote"

    if "hybrid" in text:
        return "hybrid"

    return "onsite"


# =============================
# Extract experience from JD
# =============================

def extract_experience(text):

    text = text.lower()

    # Range: "2-3 years" / "2-3 năm"
    range_pattern = re.search(r'(\d+)\s*-\s*(\d+)\+?\s*(?:year|năm)', text)
    if range_pattern:
        return f"{range_pattern.group(1)}-{range_pattern.group(2)} years"

    # Plus: "3+ years" / "3+ năm"
    plus_pattern = re.search(r'(\d+)\+\s*(?:year|năm)', text)
    if plus_pattern:
        return f"{plus_pattern.group(1)}+ years"

    # Single: "3 years" / "3 năm"
    single_pattern = re.search(r'(\d+)\s*(?:year|năm)', text)
    if single_pattern:
        return f"{single_pattern.group(1)} years"

    return None


# =============================
# Crawl JD detail
# =============================

def get_experience(driver, job_url):

    try:

        # Bỏ query string (?lab_feature=...) để lấy trang JD đầy đủ
        clean_url = job_url.split("?")[0]
        driver.get(clean_url)

        # Chờ section.job-content xuất hiện (tối đa 10s)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "section.job-content"))
            )
        except:
            print("  [warn] section.job-content not found:", clean_url)
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Tìm h2 chứa "experience" rồi lấy text từ container cha
        for h2 in soup.select("section.job-content h2"):
            if "experience" in h2.get_text().lower():
                container = h2.find_parent("div")
                text = container.get_text() if container else h2.get_text()

                result = extract_experience(text)

                if result is None:
                    print("  [warn] no experience pattern found in:", text[:120])

                return result

        print("  [warn] experience h2 not found:", clean_url)
        return None

    except Exception as e:

        print("  [error] get_experience:", e)
        return None


# =============================
# Main crawler
# =============================

def crawl_itviec(pages=3):

    driver = create_driver()

    dataset = []

    for page in range(1, pages + 1):

        url = BASE_URL + str(page)

        print("Crawling page:", page)

        driver.get(url)

        time.sleep(4)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        jobs = soup.select(".ipy-2")

        print("Jobs found:", len(jobs))

        for job in jobs:

            try:

                # title
                title_tag = job.select_one("h3")
                if not title_tag:
                    continue

                job_title = title_tag.text.strip()

                # job url (IMPORTANT)
                job_url = title_tag.get("data-url")

                # company
                company_tag = job.select_one(".imy-3 a.text-rich-grey")
                company_name = company_tag.text.strip() if company_tag else ""

                # location
                location_tag = job.select_one("div[title]")
                location = location_tag.text.strip() if location_tag else ""

                # remote
                remote_tag = job.select_one(".text-rich-grey.flex-shrink-0")
                remote_text = remote_tag.text.strip() if remote_tag else ""

                remote_option = detect_remote(remote_text)

                # salary
                salary_tag = job.select_one(".salary .ips-2")
                salary_text = salary_tag.text.strip() if salary_tag else ""

                salary_min, salary_max, currency = clean_salary(salary_text)

                # skills
                skill_tags = job.select(".itag-light")
                skills = [s.text.strip() for s in skill_tags]

                tech_stack = ", ".join(skills)

                # experience
                experience_years = None

                if job_url:
                    experience_years = get_experience(driver, job_url)

                dataset.append({

                    "job_title": job_title,
                    "company_name": company_name,
                    "location": location,
                    "remote_option": remote_option,
                    "tech_stack": tech_stack,
                    "experience_years": experience_years,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "currency": currency

                })

                print("✔", job_title, "| exp:", experience_years or "N/A")

            except Exception as e:

                print("skip:", e)

    driver.quit()

    return dataset


# =============================
# Save CSV
# =============================

def save_csv(data):

    if not data:
        print("No data collected")
        return

    keys = data[0].keys()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"itviec_jobs_{timestamp}.csv"

    # data/raw cùng cấp với src (src/data_collection -> src -> project_root -> data/raw)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(f, fieldnames=keys)

        writer.writeheader()

        writer.writerows(data)

    print("Saved:", len(data), "jobs ->", filepath)


# =============================
# Run crawler
# =============================

if __name__ == "__main__":

    jobs = crawl_itviec(20)

    save_csv(jobs)

    print("Total jobs:", len(jobs))