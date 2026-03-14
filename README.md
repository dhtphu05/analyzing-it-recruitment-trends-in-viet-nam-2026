# Phan tich va du bao xu huong tuyen dung IT tai Viet Nam

Du an nay xay dung base code cho de tai phan tich du lieu tuyen dung IT tu cac nen tang nhu ITViec, TopCV va TopDev, tu do danh gia kha nang du bao muc luong trung binh theo dac trung cong viec.

## Muc tieu

- Phan tich du lieu tuyen dung IT tai Viet Nam.
- Chuan hoa va hop nhat du lieu tu nhieu nguon crawl.
- Trich xuat ky nang, cong nghe va thong tin mo ta cong viec.
- Xay dung bai toan hoi quy de du bao `salary_avg`.

## Bien muc tieu

- `salary_avg`: muc luong trung binh sau khi quy doi va lam sach.

## Nhom dac trung chinh

- `tech_stack`
- `level`
- `experience_years`
- `location`
- `company_type`
- `skills_extracted`
- `remote_option`

## Cau truc thu muc

```text
.
|-- data/
|   |-- raw/
|   |-- interim/
|   |-- processed/
|   `-- external/
|-- docs/
|   `-- problem_statement.md
|-- notebooks/
|   `-- 01_it_recruitment_vn_project_base.ipynb
|-- reports/
|   `-- README.md
|-- src/
|   |-- data_collection/
|   |-- processing/
|   |-- analysis/
|   |-- models/
|   |-- utils/
|   `-- config.py
|-- requirements.txt
`-- README.md
```

## Quy uoc pipeline

1. Crawl tung nguon vao `data/raw/`.
2. Hop nhat va chuan hoa schema vao `data/interim/`.
3. Lam sach, trich xuat skill va tao feature vao `data/processed/`.
4. Chay EDA va trinh bay ket qua trong `notebooks/` va `reports/`.
5. Train mo hinh hoi quy du bao `salary_avg`.

## Schema goi y

Bang du lieu tong hop nen co it nhat cac cot sau:

- `job_id`
- `source`
- `job_title`
- `company_name`
- `location`
- `company_type`
- `level`
- `experience_years`
- `salary_min`
- `salary_max`
- `salary_avg`
- `salary_currency`
- `job_description`
- `skills_extracted`
- `posted_date`
- `job_url`

## Phan cong de xuat

- Data Engineer: phat trien crawler, xu ly pagination, luu raw data.
- Data Processor & NLP Specialist: cleaning, skill extraction, feature engineering.
- Data Analyst & Visualizer: EDA, visualization, nhan xet, ket luan.

## Cach bat dau

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Sau do co the chay tung buoc rieng le, vi du:

```bash
python3 src/data_collection/merge_raw_data.py --input-dir data/raw --output data/interim/jobs_merged.csv
python3 src/processing/clean_jobs.py --input data/interim/jobs_merged.csv --output data/processed/jobs_cleaned.csv
python3 src/processing/extract_skills.py --input data/processed/jobs_cleaned.csv --output data/processed/jobs_features.csv
python3 src/models/train_salary_regressor.py --input data/processed/jobs_features.csv
```

## Ghi chu

- Hai notebook `911 Calls` dang co trong workspace la tai lieu cu, khong thuoc de tai nay.
- Base project nay chi tao bo khung va cac script starter; phan crawl thuc te can bo sung selector HTML va logic chong block theo tung trang.
