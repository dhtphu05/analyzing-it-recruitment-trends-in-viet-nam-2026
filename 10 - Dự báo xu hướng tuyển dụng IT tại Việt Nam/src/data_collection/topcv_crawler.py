import re
import time
import csv
import os
import random
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup


BASE_URL = "https://www.topcv.vn/tim-viec-lam-software-engineering-cr257cb258?page="


# =============================
# Create driver
# =============================

def create_driver():
    """
    Kết nối vào Chrome đang chạy sẵn (đã đăng nhập).

    Trước khi chạy script, mở Chrome bằng lệnh sau (chạy trong cmd):
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9223 --user-data-dir="C:\\ChromeSessionTopCV"
    """
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9223")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver


# =============================
# Helpers
# =============================

def clean_salary(text):
    if not text:
        return None, None, None

    text = text.lower().replace(",", "").strip()
    nums = re.findall(r"\d+(?:\.\d+)?", text)

    if not nums:
        return None, None, None

    nums = [float(n) for n in nums]

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
    return int(nums[0]) if nums else None


def parse_posted_days(text):
    if not text:
        return None
    text = text.strip().lower()
    nums = re.findall(r"\d+", text)
    if not nums:
        return 0
    val = int(nums[0])
    if "phút" in text or "giờ" in text:
        return 0
    if "ngày" in text:
        return val
    if "tuần" in text:
        return val * 7
    if "tháng" in text:
        return val * 30
    return None

def _get_filepath():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

FIELDNAMES = [
    "job_title", "tech_stack", "experience_years", "location", "company_name",
    "remote_option", "salary_min", "salary_max", "currency",
    "posted_date", "deadline", "job_description",
]

def append_csv(rows, filepath):
    if not rows:
        return
    file_exists = os.path.isfile(filepath)
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    print(f"  → Appended {len(rows)} rows → {filepath}")


# =============================
# Phase 1 — Collect job URLs & posted date
# =============================

def collect_job_urls(driver, start_page=1, pages=5):
    collected = []
    seen_ids = set()

    for page in range(start_page, start_page + pages):
        url = BASE_URL + str(page)
        print(f"[Phase 1] Page {page}: {url}")

        driver.get(url)
        # Giả lập người dùng chờ từ 1 đến 2 giây lúc mở search list 
        time.sleep(random.uniform(1.0, 2.0))
        
        # Cuộn ngẫu nhiên
        scroll_steps = random.randint(1, 3)
        for _ in range(scroll_steps):
            driver.execute_script(f"window.scrollBy(0, {random.randint(300, 700)});")
            time.sleep(random.uniform(0.2, 0.5))
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(0.5, 1.0))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_cards = soup.select(".job-item-search-result")

        if not job_cards:
            print("  No job cards found – stopping.")
            break

        for card in job_cards:
            job_id = card.get("data-job-id", "").strip()
            if not job_id or job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            link_tag = card.select_one("h3.title a")
            if not link_tag:
                link_tag = card.select_one(f'a[href*="/{job_id}.html"]')
            job_url = link_tag["href"].split("?")[0] if link_tag and link_tag.get("href") else ""

            posted_tag = card.select_one(".label-update")
            if posted_tag:
                raw_posted = posted_tag.get_text(" ", strip=True)
                raw_posted = re.sub(r"(đăng|cập nhật)", "", raw_posted, flags=re.IGNORECASE).strip()
            else:
                raw_posted = ""

            posted_days_ago = parse_posted_days(raw_posted)

            collected.append({
                "job_id": job_id,
                "job_url": job_url,
                "posted_days_ago": posted_days_ago,
                "posted_raw": raw_posted,
            })
            print(f"  ✔ job_id={job_id}  posted={raw_posted!r}")

    print(f"\n[Phase 1] Collected {len(collected)} job URLs.\n")
    return collected


# =============================
# Phase 2 — Crawl each JD page
# =============================

def crawl_job_detail(driver, job_url):
    driver.get(job_url)
    
    # Sleep ngắn hơn khi mở trang JD
    time.sleep(random.uniform(1.0, 2.0))

    # Cuộn chính xác 4 lần để xuống hết trang
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    step = scroll_height / 4
    for i in range(1, 5):
        driver.execute_script(f"window.scrollTo(0, {step * i});")
        time.sleep(random.uniform(0.3, 0.8))

    soup = BeautifulSoup(driver.page_source, "html.parser")
    body = soup.select_one(".job-detail__body")
    if not body:
        return None

    title_tag = body.select_one("h1.job-detail__info--title")
    job_title = title_tag.get_text(" ", strip=True) if title_tag else ""
    salary_tag = body.select_one(".section-salary .job-detail__info--section-content-value")
    salary_text = salary_tag.text.strip() if salary_tag else ""
    salary_min, salary_max, currency = clean_salary(salary_text)

    location_tag = body.select_one(".section-location .job-detail__info--section-content-value a")
    if not location_tag:
        location_tag = body.select_one(".section-location .job-detail__info--section-content-value")
    location = location_tag.text.strip() if location_tag else ""

    exp_tag = body.select_one(".section-experience .job-detail__info--section-content-value")
    exp_text = exp_tag.text.strip() if exp_tag else ""
    experience_years = parse_experience(exp_text)

    deadline_tag = body.select_one(".job-detail__info--deadline-date")
    deadline = deadline_tag.text.strip() if deadline_tag else ""

    job_description = ""
    for item in body.select(".job-description__item"):
        h3 = item.select_one("h3")
        content_div = item.select_one(".job-description__item--content")
        if h3 and content_div:
            if "mô tả" in h3.get_text(strip=True).lower():
                job_description = content_div.get_text("\n", strip=True)
                break

    skills = []
    for tag_group in body.select(".job-tags__group"):
        group_name_el = tag_group.select_one(".job-tags__group-name")
        if group_name_el and "chuyên môn" in group_name_el.text.strip().lower():
            for a in tag_group.select("a.item"):
                skill = a.text.strip()
                if skill and "..." not in skill:
                    skills.append(skill)

    tech_stack = ", ".join(skills)

    img_tag = soup.select_one(".company-name img")
    if img_tag:
        company_name = img_tag.get('alt')
    else:
        company_name = ""

    return {
        "job_title":        job_title,
        "tech_stack":       tech_stack,
        "experience_years": experience_years,
        "location":         location,
        "company_name":     company_name,
        "salary_min":       salary_min,
        "salary_max":       salary_max,
        "currency":         currency,
        "deadline":         deadline,
        "job_description":  job_description,
    }


# =============================
# Main crawler
# =============================

def crawl_topcv(total_pages=12, batch_size=2):

    driver = create_driver()
    today = datetime.now().date()
    dataset = []
    batch_results = []
    seen_urls = set()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(_get_filepath(), f"topcv_jobs_{timestamp}.csv")
    print(f"[Output] {filepath}\n")

    try:
        end_page = 1 + total_pages
        for start_page in range(1, end_page, batch_size):
            batch_num = (start_page - 1) // batch_size + 1
            print(f"\n{'='*60}")
            print(f"[Batch {batch_num}] Pages {start_page} → {start_page + batch_size - 1}")
            print(f"{'='*60}")

            # Phase 1: thu thập URLs và crawl ngày đăng job cho batch này
            url_records_raw = collect_job_urls(driver, start_page=start_page, pages=batch_size)
            
            # Loại bỏ trùng lặp giữa các batch
            url_records = []
            for r in url_records_raw:
                if r["job_url"] not in seen_urls:
                    seen_urls.add(r["job_url"])
                    url_records.append(r)

            print(f"\n[Phase 1 Batch {batch_num}] {len(url_records)} URLs mới → starting Phase 2\n")

            batch_results = []
            total = len(url_records)
            for idx, rec in enumerate(url_records, 1):
                job_url = rec["job_url"]
                if not job_url:
                    continue

                print(f"[Phase 2] ({idx}/{total}) {job_url}")
                detail = crawl_job_detail(driver, job_url)

                if detail:
                    days_ago = rec["posted_days_ago"]
                    posted_date = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d") if days_ago is not None else ""

                    record = {
                        "job_title":        detail["job_title"],
                        "tech_stack":       detail["tech_stack"],
                        "experience_years": detail["experience_years"],
                        "location":         detail["location"],
                        "company_name":     detail["company_name"],
                        "remote_option":    "onsite",
                        "salary_min":       detail["salary_min"],
                        "salary_max":       detail["salary_max"],
                        "currency":         detail["currency"],
                        "posted_date":      posted_date,
                        "deadline":         detail["deadline"],
                        "job_description":  detail["job_description"],
                    }
                    batch_results.append(record)
                    dataset.append(record)
                    print(f"  ✔ {record['job_title']}")
                else:
                    print(f"  ✗ Skipped (no data)")

            append_csv(batch_results, filepath)
            batch_results = []
            print(f"[Batch {batch_num} done] Total jobs so far: {len(dataset)}")

            if start_page + batch_size <= total_pages:
                # break time giữa các batch lớn để tránh bị đánh giá là bot
                break_time = random.uniform(10.0, 20.0)
                print(f"\n[!] Tạm nghỉ {break_time:.1f} giây để tránh anti-bot...")
                time.sleep(break_time)

    except KeyboardInterrupt:
        append_csv(batch_results, filepath)
        print(f"\n[!] Ctrl+C — đã lưu {len(dataset)} jobs vào {filepath}")

    except Exception as e:
        append_csv(batch_results, filepath)
        print(f"\n[!] Lỗi không mong muốn: {e} — đã lưu {len(dataset)} jobs vào {filepath}")

    finally:
        print(f"\n[Done] Tổng cộng: {len(dataset)} jobs → {filepath}")

    return dataset, filepath


# =============================
# Run crawler
# =============================

if __name__ == "__main__":
    jobs, out_file = crawl_topcv(total_pages=12, batch_size=2)
    print("Total jobs:", len(jobs))
