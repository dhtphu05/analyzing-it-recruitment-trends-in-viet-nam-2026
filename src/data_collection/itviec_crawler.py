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


BASE_URL = "https://itviec.com/it-jobs?page="


# =============================
# Create driver
# =============================

def create_driver():
    """
    Kết nối vào Chrome đang chạy sẵn (đã đăng nhập itviec).

    Trước khi chạy script, mở Chrome bằng lệnh sau (chạy trong cmd):
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\\ChromeSession"

    Sau đó đăng nhập itviec.com, rồi mới chạy script này.
    """
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

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


def detect_remote(text):

    text = text.lower()

    if "remote" in text:
        return "remote"

    if "hybrid" in text:
        return "hybrid"

    return "onsite"


def extract_experience(text):

    text = text.lower()

    # "2-3 years" / "2-3 năm"
    range_pattern = re.search(r'(\d+)\s*-\s*(\d+)\+?\s*(?:year|năm)', text)
    if range_pattern:
        return f"{range_pattern.group(1)}-{range_pattern.group(2)} years"

    # "3+ years" / "3+ năm"
    plus_pattern = re.search(r'(\d+)\+\s*(?:year|năm)', text)
    if plus_pattern:
        return f"{plus_pattern.group(1)}+ years"

    # "3 years" / "3 năm"
    single_pattern = re.search(r'(\d+)\s*(?:year|năm)', text)
    if single_pattern:
        return f"{single_pattern.group(1)} years"

    return None

FIELDNAMES = [
    "job_title", "tech_stack", "experience_years", "location", "company_name",
    "company_type", "company_industry", "remote_option",
    "salary_min", "salary_max", "currency",
    "posted_date", "job_description",
]


def _get_filepath():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def append_csv(rows, filepath):
    """Ghi thêm rows vào filepath. Tạo header nếu file chưa tồn tại."""
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
# Phase 1 — Collect job URLs
# =============================
def collect_job_urls(driver, start_page=1, pages=10):
    all_urls = []

    for page in range(start_page, start_page + pages):

        url = BASE_URL + str(page)
        print(f"[Phase 1] Collecting URLs from page {page}...")

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

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-card h3[data-url]"))
            )
        except Exception:
            print(f"  [warn] No job cards on page {page} - skipping")
            continue

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for h3 in soup.select("div.job-card h3[data-url]"):
            job_url = h3.get("data-url", "")
            if job_url:
                # Bỏ query string để lấy trang JD đầy đủ
                clean_url = job_url.split("?")[0]
                if clean_url not in all_urls:
                    all_urls.append(clean_url)

        print(f"  → {len(all_urls)} URLs collected so far")

    return all_urls


# =============================
# Phase 2 — Crawl each JD page
# =============================

def crawl_job_detail(driver, job_url):
    """
    Vào trang JD detail, lấy toàn bộ thông tin từ một trang duy nhất.
    Trang detail render đầy đủ (không lazy-load), nên không cần scroll.
    """
    try:
        driver.get(job_url)

        # Sleep ngắn hơn khi mở trang JD
        time.sleep(random.uniform(1.0, 2.0))

        # Cuộn chính xác 4 lần để xuống hết trang
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        step = scroll_height / 4
        for i in range(1, 5):
            driver.execute_script(f"window.scrollTo(0, {step * i});")
            time.sleep(random.uniform(0.3, 0.8))
            
        # Chờ phần header JD xuất hiện
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-show-header"))
            )
        except Exception:
            print(f"  [warn] Job header not found: {job_url}")
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")

        title_tag = soup.select_one(".job-show-header h1")
        if not title_tag:
            return None
        job_title = title_tag.text.strip()

        company_tag = soup.select_one(".employer-name")
        company_name = company_tag.text.strip() if company_tag else ""

        company_type = ""
        company_industry = ""
        employer_section = soup.select_one("section.job-show-employer-info")
        if employer_section:
            for row in employer_section.select("div.row.gx-0"):
                cols = row.select("div.col")
                if len(cols) >= 2:
                    label = cols[0].get_text(strip=True).lower()
                    value = cols[1].get_text(strip=True)
                    if "company type" in label:
                        company_type = value
                    elif "company industry" in label:
                        company_industry = value

        salary_container = soup.select_one("div.salary")
        salary_tag = salary_container.select_one("span.ips-2.fw-500") if salary_container else None
        salary_text = salary_tag.text.strip() if salary_tag else ""
        salary_min, salary_max, currency = clean_salary(salary_text)

        remote_option = "onsite"
        posted_date = datetime.now().strftime("%Y-%m-%d")
        for item in soup.select(".preview-header-item"):
            span = item.select_one("span.normal-text.text-rich-grey")
            if not span:
                continue
            span_text = span.text.strip()
            if "posted" in span_text.lower():
                days_match = re.search(r"(\d+)\s*day", span_text.lower())
                if days_match:
                    posted_date = (datetime.now() - timedelta(days=int(days_match.group(1)))).strftime("%Y-%m-%d")
            else:
                remote_option = detect_remote(span_text)

        location = ""
        for div in soup.select("div.d-inline-block.text-dark-grey"):
            span = div.select_one("span.normal-text.text-rich-grey")
            if span and not div.select_one(".preview-header-item"):
                full_location = span.text.strip()
                location = full_location.split(",")[-1].strip()
                break

        tech_stack = ""
        for section in soup.select("div.imb-4.imb-xl-3"):
            label = section.select_one("div.w-xl-fixed-100")
            if label and "skills" in label.text.lower():
                skill_tags = section.select("a.itag-light")
                skills = [s.text.strip() for s in skill_tags]
                tech_stack = ", ".join(skills)
                break

        experience_years = None
        job_description = ""
        for h2 in soup.select("section.job-content h2"):
            h2_text = h2.get_text().lower()
            if "experience" in h2_text:
                container = h2.find_parent("div")
                text = container.get_text() if container else h2.get_text()
                experience_years = extract_experience(text)
            if "job description" in h2_text:
                container = h2.find_parent("div")
                if container:
                    job_description = container.get_text(separator=" ", strip=True)

        return {
            "job_title": job_title,
            "tech_stack": tech_stack,
            "experience_years": experience_years,
            "location": location,
            "company_name": company_name,
            "company_type": company_type,
            "company_industry": company_industry,
            "remote_option": remote_option,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "currency": currency,
            "posted_date": posted_date,
            "job_description": job_description,
        }

    except Exception as e:
        print(f"  [error] crawl_job_detail({job_url}): {e}")
        return None


# =============================
# Main crawler
# =============================

def crawl_itviec(total_pages=60, batch_size=10):

    driver = create_driver()
    dataset = []
    seen_urls = set()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(_get_filepath(), f"itviec_jobs_{timestamp}.csv")
    print(f"[Output] {filepath}\n")

    try:
        for start_page in range(1, total_pages + 1, batch_size):
            batch_num = (start_page - 1) // batch_size + 1
            print(f"\n{'='*60}")
            print(f"[Batch {batch_num}] Pages {start_page} → {start_page + batch_size - 1}")
            print(f"{'='*60}")

            # Phase 1: thu thập URLs cho batch này
            batch_urls_raw = collect_job_urls(driver, start_page=start_page, pages=batch_size)
            batch_urls = [u for u in batch_urls_raw if u not in seen_urls]
            seen_urls.update(batch_urls)
            print(f"\n[Phase 1 Batch {batch_num}] {len(batch_urls)} URLs mới → starting Phase 2\n")

            # Phase 2: crawl từng JD trong batch
            batch_results = []
            for i, job_url in enumerate(batch_urls, 1):
                print(f"[Phase 2] {i}/{len(batch_urls)} — {job_url}")

                record = crawl_job_detail(driver, job_url)

                if record:
                    dataset.append(record)
                    append_csv([record], filepath)
                    
                    tech_preview = (record["tech_stack"][:40] + "...") if len(record["tech_stack"]) > 40 else (record["tech_stack"] or "N/A")
                    print(f"  ✔ {record['job_title'][:50]}")
                    print(f"    tech: {tech_preview}")
                    print(f"    exp: {record['experience_years'] or 'N/A'} | salary: {record['salary_min']}-{record['salary_max']} {record['currency'] or ''}")

            print(f"[Batch {batch_num} done] Total jobs so far: {len(dataset)}")

            if start_page + batch_size <= total_pages:
                # break time giữa các batch lớn để tránh bị đánh giá là bot
                break_time = random.uniform(10.0, 20.0)
                print(f"\n[!] Tạm nghỉ {break_time:.1f} giây để tránh anti-bot...")
                time.sleep(break_time)

    except KeyboardInterrupt:
        print(f"\n[!] Ctrl+C — đã lưu {len(dataset)} jobs vào {filepath}")

    except Exception as e:
        print(f"\n[!] Lỗi không mong muốn: {e} — đã lưu {len(dataset)} jobs vào {filepath}")

    finally:
        try:
            driver.quit()
        except Exception:
            pass
        print(f"\n[Done] Tổng cộng: {len(dataset)} jobs → {filepath}")

    return dataset, filepath


# =============================
# Run crawler
# =============================

if __name__ == "__main__":

    jobs, out_file = crawl_itviec(total_pages=60, batch_size=10)

    print("Total jobs:", len(jobs))

