# Phan tich va du bao xu huong tuyen dung IT tai Viet Nam

Du an nay duoc thuc hien de dap ung yeu cau giua ky: **tu crawl du lieu**, lam sach, truc quan hoa va danh gia tinh kha thi cua bai toan du bao muc luong trong thi truong tuyen dung IT tai Viet Nam.

## 1. Phat bieu bai toan

Muc tieu cua nhom la phan tich du lieu tuyen dung thu thap tu cac nen tang cong nghe nhu ITViec, TopCV va TopDev de khao sat kha nang xay dung mo hinh du doan bien muc tieu `Y` tu tap dac trung `X_i`.

- Bien muc tieu `Y`: `salary_avg`
- Loai bai toan: `Regression`
- Ly do: `salary_avg` la bien so thuc lien tuc

## 2. Danh gia tinh kha thi

Bai toan co tinh kha thi ve du lieu vi:

- Tin tuyen dung thuong chua cac truong thong tin co y nghia nhu muc luong, cap bac, ky nang, kinh nghiem, dia diem, loai hinh cong ty.
- Cac bien tren co the duoc chuan hoa, ma hoa va dung de phan tich moi quan he voi luong.
- Neu du lieu crawl duoc lon hon 1000 mau va co it nhat 5 bien mo ta, nhom co du co so de danh gia bai toan.

## 3. Tap dac trung du kien

- `job_title`
- `tech_stack`
- `skills_extracted`
- `level`
- `experience_years`
- `location`
- `company_type`
- `remote_option`
- `salary_min`
- `salary_max`
- `salary_avg`

## 4. Cau truc folder nop bai

Folder nop bai nen dat ten theo quy tac:

`STTnhom - Phan tich va du bao xu huong tuyen dung IT tai Viet Nam`

Cau truc de xuat:

```text
STTnhom - Phan tich va du bao xu huong tuyen dung IT tai Viet Nam/
|-- README.md
|-- notebooks/
|   |-- 01_data_collection_and_cleaning.ipynb
|   |-- 02_eda_and_visualization.ipynb
|   `-- 03_midterm_submission_final.ipynb
|-- src/
|   |-- data_collection/
|   |   |-- itviec_crawler.py
|   |   |-- topcv_crawler.py
|   |   |-- topdev_crawler.py
|   |   `-- merge_raw_data.py
|   |-- processing/
|   |   |-- clean_jobs.py
|   |   `-- extract_skills.py
|   `-- analysis/
|       |-- eda.py
|       `-- visualize.py
|-- raw data/
|   |-- itviec_jobs.json
|   |-- topcv_jobs.json
|   |-- topdev_jobs.json
|   `-- jobs_merged_raw.csv
|-- clean data/
|   |-- jobs_cleaned.csv
|   `-- jobs_features.csv
|-- docs/
|   |-- problem_statement.md
|   `-- team_roles.md
`-- reports/
    |-- eda_salary_distribution.png
    |-- correlation_heatmap.png
    |-- skills_clustermap.png
    `-- tsne_visualization.png
```

## 5. Trinh tu thuc hien

1. Crawl du lieu tu ITViec, TopCV, TopDev va luu vao `raw data/`.
2. Hop nhat du lieu tho thanh mot bang tong hop.
3. Lam sach du lieu, bo trung lap, xu ly null, chuan hoa salary va luu vao `clean data/`.
4. Trich xuat ky nang, tao them feature va ma hoa category/text.
5. Truc quan hoa du lieu don bien va da bien tren notebook.
6. Viet nhan xet, ket luan va tai lieu tham khao bang Markdown trong notebook.

## 6. Huong dan chay chuong trinh

Tao moi truong va cai thu vien:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Chay cac buoc xu ly co ban:

```bash
python3 src/data_collection/itviec_crawler.py --pages 10 --output "raw data/itviec_jobs.json"
python3 src/data_collection/topcv_crawler.py --pages 10 --output "raw data/topcv_jobs.json"
python3 src/data_collection/topdev_crawler.py --pages 10 --output "raw data/topdev_jobs.json"
python3 src/data_collection/merge_raw_data.py --input-dir "raw data" --output "raw data/jobs_merged_raw.csv"
python3 src/processing/clean_jobs.py --input "raw data/jobs_merged_raw.csv" --output "clean data/jobs_cleaned.csv"
python3 src/processing/extract_skills.py --input "clean data/jobs_cleaned.csv" --output "clean data/jobs_features.csv"
```

Sau khi co du lieu, mo notebook de trinh bay:

- `notebooks/01_data_collection_and_cleaning.ipynb`
- `notebooks/02_eda_and_visualization.ipynb`
- `notebooks/03_midterm_submission_final.ipynb`

## 7. Vai tro tung thanh vien

### Thanh vien 1 - Data Engineer

Phu trach crawl va hop nhat du lieu.

Can hoan thanh:

- Viet script crawl cho ITViec, TopCV, TopDev
- Ghi ro cach thu thap du lieu trong notebook
- Dam bao tong so mau > 1000
- Luu du lieu vao `raw data/`

Can trinh bay khi bao cao:

- Nguon du lieu
- Cach crawl
- So mau thu duoc
- Cac kho khan khi crawl

Phan phu trach trong notebook tong:

- Muc `Thu thap du lieu`
- Muc `Mo ta nguon du lieu`
- Muc `So luong mau, so bien, cach crawl`
- Phan mo ta schema du lieu ban dau

### Thanh vien 2 - Data Processor va NLP Specialist

Phu trach cleaning, encoding va feature engineering.

Can hoan thanh:

- Xu ly null, duplicate, salary format, location, level, experience
- Tao `salary_avg`
- Trich xuat skill tu `job_title` va `job_description`
- Tao feature moi va luu vao `clean data/`

Can trinh bay khi bao cao:

- Du lieu truoc va sau cleaning khac nhau the nao
- Cach chuan hoa salary
- Cach ma hoa category/text
- Feature moi nao duoc tao ra

Phan phu trach trong notebook tong:

- Muc `Lam sach va chuan hoa du lieu`
- Muc `Ma hoa du lieu va xu ly ngon ngu tu nhien`
- Muc `Feature engineering`
- Phan so sanh phan bo du lieu truoc va sau cleaning

### Thanh vien 3 - Data Analyst va Visualizer

Phu trach EDA, bieu do, nhan xet va ket luan.

Can hoan thanh:

- Thong ke mo ta don bien
- Ve histogram, countplot, boxplot, scatter plot, heatmap, clustermap
- Thu nghiem t-SNE neu du lieu da duoc ma hoa
- Viet ket luan danh gia tinh kha thi cua bai toan

Can trinh bay khi bao cao:

- Moi bieu do tra loi cau hoi gi
- Xu huong luong theo level, ky nang, dia diem
- Dac trung nao co y nghia nhat
- Bai toan co kha thi hay khong

Phan phu trach trong notebook tong:

- Muc `Thong ke mo ta va truc quan hoa don bien`
- Muc `Truc quan hoa moi quan he da bien`
- Muc `Truc quan hoa khong gian du lieu nhieu chieu`
- Muc `Danh gia tinh kha thi cua bai toan`
- Muc `Ket luan`
- Muc `Tai lieu tham khao`

## 8. Checklist truoc khi nop

- Co file `README.md`
- Co thu muc `raw data`
- Co thu muc `clean data`
- Co notebook de trinh bay bai lam
- Co ma nguon crawl du lieu
- Co mo ta quy trinh cleaning
- Co truc quan hoa du lieu
- Co nhan xet va ket luan
- Co tai lieu tham khao
- Tong dung luong folder nho hon 20 MB

## 9. Ghi chu

- Hai file `911 Calls` trong workspace la tai lieu cu, khong thuoc bo bai nop nay.
- File notebook nop chinh nen dung [notebooks/02_midterm_submission_template.ipynb](/Users/mac/Desktop/SEM_6/KHDL/GKY/notebooks/02_midterm_submission_template.ipynb) lam khung de phat trien thanh ban cuoi.
