# Phân tích dữ liệu tuyển dụng IT tại Việt Nam

Đây là bài làm giữa kỳ của nhóm về dữ liệu tuyển dụng IT tại Việt Nam. Dữ liệu được nhóm tự crawl từ ITViec và TopCV, sau đó làm sạch, trích xuất skill và đưa vào notebook để phân tích.

Notebook chính là `description.ipynb`. Trong notebook, nhóm làm theo hướng phân tích dữ liệu và phân cụm trên toàn bộ dữ liệu sạch. Ngoài ra, nhóm tách riêng một tập con có lương để xem thêm khả năng làm hồi quy với `salary_avg`.

Hiện tại dữ liệu raw có `1415` mẫu, trong đó `997` mẫu từ ITViec và `418` mẫu từ TopCV. Sau khi làm sạch còn `1393` mẫu trong `jobs_cleaned.csv`. File `jobs_features.csv` cũng có `1393` mẫu, và tập con có lương `jobs_salary_subset.csv` có `527` mẫu.

Các file chính trong bài làm:

- `description.ipynb`: notebook trình bày bài làm
- `src/data_collection/itviec_crawler.py`: mã crawl ITViec
- `src/data_collection/topcv_crawler.py`: mã crawl TopCV
- `src/processing/clean_jobs.py`: làm sạch và chuẩn hóa dữ liệu
- `src/processing/extract_skills.py`: trích xuất skill và tạo feature
- `raw data/`: dữ liệu thô sau khi crawl
- `clean data/`: dữ liệu sau khi làm sạch và tạo feature

Nếu muốn chạy lại, có thể tạo môi trường và cài thư viện:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas beautifulsoup4 requests selenium webdriver-manager matplotlib seaborn scikit-learn nbformat nbclient ipykernel plotly
```

Nếu muốn tạo lại file clean và feature:

```bash
python3 src/processing/clean_jobs.py --input-dir "raw data" --output "clean data/jobs_cleaned.csv"
python3 src/processing/extract_skills.py --input "clean data/jobs_cleaned.csv" --output "clean data/jobs_features.csv"
```

Sau đó mở notebook:

```bash
jupyter notebook description.ipynb
```

Trong notebook hiện có các phần chính như: phát biểu bài toán, mô tả dữ liệu, cleaning, feature engineering, trực quan hóa đơn biến và đa biến, t-SNE, kết luận về tính khả thi của dữ liệu, và một phần ngắn khảo sát tập con có lương.
