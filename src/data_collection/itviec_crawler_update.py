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
# Extract experience from text
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
# Phase 1 — Collect job URLs
# =============================

def collect_job_urls(driver, pages=3):
    """
    Duyệt qua các trang listing, thu thập toàn bộ job URLs.
    Không cần parse chi tiết, chỉ cần lấy link.
    """
    all_urls = []

    for page in range(1, pages + 1):

        url = BASE_URL + str(page)
        print(f"[Phase 1] Collecting URLs from page {page}...")

        driver.get(url)
        time.sleep(2)

        # Scroll nhanh để trigger lazy-load cards
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

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

        # Chờ phần header JD xuất hiện
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job-show-header"))
            )
        except Exception:
            print(f"  [warn] Job header not found: {job_url}")
            return None

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # ── title
        title_tag = soup.select_one(".job-show-header h1")
        if not title_tag:
            return None
        job_title = title_tag.text.strip()

        # ── company
        company_tag = soup.select_one(".employer-name")
        company_name = company_tag.text.strip() if company_tag else ""

        # ── salary
        salary_container = soup.select_one("div.salary")
        salary_tag = salary_container.select_one("span.ips-2.fw-500") if salary_container else None
        salary_text = salary_tag.text.strip() if salary_tag else ""
        salary_min, salary_max, currency = clean_salary(salary_text)

        # ── remote/work type — "At office" / "Hybrid" / "Remote"
        # Lấy từ phần preview-header-item có icon người
        remote_option = "onsite"
        for item in soup.select(".preview-header-item"):
            span = item.select_one("span.normal-text.text-rich-grey")
            if span:
                remote_option = detect_remote(span.text.strip())
                break

        # ── location — địa chỉ cụ thể (hoặc thành phố)
        location = ""
        for div in soup.select("div.d-inline-block.text-dark-grey"):
            span = div.select_one("span.normal-text.text-rich-grey")
            if span and not div.select_one(".preview-header-item"):
                full_location = span.text.strip()
                # Lấy phần text cuối cùng sau dấu phẩy (thường là Tỉnh/Thành phố)
                location = full_location.split(",")[-1].strip()
                break
        # Fallback: lấy từ job-by-city trong data-layer attribute
        if not location:
            apply_btn = soup.select_one("a[data-jobs--data-layer-params-value]")
            if apply_btn:
                import json
                try:
                    params = json.loads(apply_btn.get("data-jobs--data-layer-params-value", "{}"))
                    location = params.get("job_by_city", "")
                except Exception:
                    pass

        # ── tech_stack (Skills section trên trang JD)
        # Trang detail có section "Skills:" với các itag-light
        # Cấu trúc: div.imb-4 > div.w-xl-fixed-100 "Skills:" + div.d-flex > a.itag-light
        tech_stack = ""
        for section in soup.select("div.imb-4.imb-xl-3"):
            label = section.select_one("div.w-xl-fixed-100")
            if label and "skills" in label.text.lower():
                skill_tags = section.select("a.itag-light")
                skills = [s.text.strip() for s in skill_tags]
                tech_stack = ", ".join(skills)
                break

        # Fallback nếu không tìm thấy section Skills:
        if not tech_stack:
            # Lấy từ data-layer params (job_required_skill)
            apply_btn = soup.select_one("a[data-jobs--data-layer-params-value]")
            if apply_btn:
                import json
                try:
                    params = json.loads(apply_btn.get("data-jobs--data-layer-params-value", "{}"))
                    tech_stack = params.get("job_required_skill", "")
                except Exception:
                    pass

        # ── experience — tìm trong section "Your skills and experience"
        experience_years = None
        for h2 in soup.select("section.job-content h2"):
            if "experience" in h2.get_text().lower():
                container = h2.find_parent("div")
                text = container.get_text() if container else h2.get_text()
                experience_years = extract_experience(text)
                break

        return {
            "job_title": job_title,
            "tech_stack": tech_stack,
            "experience_years": experience_years,
            "location": location,
            "company_name": company_name,
            "remote_option": remote_option,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "currency": currency,
        }

    except Exception as e:
        print(f"  [error] crawl_job_detail({job_url}): {e}")
        return None


# =============================
# Main crawler
# =============================

def crawl_itviec(pages=3):

    driver = create_driver()
    dataset = []

    try:

        # ── Phase 1: Thu thập toàn bộ URLs từ listing pages
        job_urls = collect_job_urls(driver, pages)
        print(f"\n[Phase 1 done] Total URLs: {len(job_urls)}\n")

        # ── Phase 2: Crawl từng JD detail page
        for i, job_url in enumerate(job_urls, 1):

            print(f"[Phase 2] {i}/{len(job_urls)} — {job_url}")

            record = crawl_job_detail(driver, job_url)

            if record:
                dataset.append(record)
                tech_preview = (record["tech_stack"][:40] + "...") if len(record["tech_stack"]) > 40 else (record["tech_stack"] or "N/A")
                print(f"  ✔ {record['job_title'][:50]}")
                print(f"    tech: {tech_preview}")
                print(f"    exp: {record['experience_years'] or 'N/A'} | salary: {record['salary_min']}-{record['salary_max']} {record['currency'] or ''}")

    except KeyboardInterrupt:
        print("\n[!] Cắt bởi người dùng (Ctrl+C) — đang lưu dữ liệu đã thu thập...")

    except Exception as e:
        print(f"\n[!] Lỗi không mong muốn: {e} — đang lưu dữ liệu đã thu thập...")

    finally:
        try:
            driver.quit()
        except Exception:
            pass

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

    # data/raw cùng cấp với src
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    output_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    print(f"Saved: {len(data)} jobs → {filepath}")


# =============================
# Run crawler
# =============================

if __name__ == "__main__":

    jobs = crawl_itviec(20)

    save_csv(jobs)

    print("Total jobs:", len(jobs))
