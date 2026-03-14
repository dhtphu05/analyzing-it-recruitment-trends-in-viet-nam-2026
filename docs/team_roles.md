# Phan cong cong viec trong nhom

Tai lieu nay dung de thong nhat vai tro, dau ra va cach moi thanh vien trinh bay trong luc bao cao.

## Muc tieu chung

Ca nhom phai nop mot folder co:

- `README.md`
- `raw data/`
- `clean data/`
- notebook trinh bay bai lam
- ma nguon crawl va xu ly

Tat ca du lieu phai la du lieu nhom **tu crawl**, so mau phai **> 1000**, va notebook phai co day du phat bieu bai toan, cleaning, truc quan hoa, nhan xet va ket luan.

## Thanh vien 1 - Data Engineer

### Cong viec phai lam

- Crawl du lieu tu ITViec, TopCV, TopDev
- Xu ly pagination va luu file raw
- Hop nhat du lieu tho thanh file tong hop
- Ghi lai nguon crawl, ngay crawl, so mau moi nguon

### File phu trach

- `src/data_collection/itviec_crawler.py`
- `src/data_collection/topcv_crawler.py`
- `src/data_collection/topdev_crawler.py`
- `src/data_collection/merge_raw_data.py`
- `raw data/itviec_jobs.json`
- `raw data/topcv_jobs.json`
- `raw data/topdev_jobs.json`
- `raw data/jobs_merged_raw.csv`

### Noi dung phai noi khi thuyet trinh

- Crawl tu website nao
- Lay cac truong gi
- So mau thu duoc bao nhieu
- Cach dam bao du lieu do nhom tu thu thap

### Phan phai viet trong notebook tong

- `3. Thu thap du lieu`
- Mo ta nguon crawl, ngay crawl, cach crawl
- Bang tong hop so mau theo tung nguon
- Mo ta schema du lieu raw

## Thanh vien 2 - Data Processor va NLP Specialist

### Cong viec phai lam

- Lam sach du lieu va bo trung lap
- Chuan hoa cot salary
- Tao `salary_avg`
- Chuan hoa `location`, `level`, `experience_years`
- Trich xuat ky nang tu text
- Ma hoa category va tao feature moi

### File phu trach

- `src/processing/clean_jobs.py`
- `src/processing/extract_skills.py`
- `clean data/jobs_cleaned.csv`
- `clean data/jobs_features.csv`

### Noi dung phai noi khi thuyet trinh

- Du lieu loi duoc xu ly the nao
- Salary duoc chuyen doi ra sao
- Encoding/NLP duoc lam bang cach nao
- Cac feature moi nao quan trong cho bai toan

### Phan phai viet trong notebook tong

- `6. Lam sach va chuan hoa du lieu`
- `7. Ma hoa du lieu va xu ly ngon ngu tu nhien`
- `8. Feature engineering`
- Phan minh hoa truoc va sau cleaning

## Thanh vien 3 - Data Analyst va Visualizer

### Cong viec phai lam

- Tao thong ke mo ta cho du lieu
- Ve bieu do don bien va da bien
- Ve heatmap, boxplot, scatter plot, clustermap
- Thu nghiem t-SNE neu co du lieu da ma hoa
- Viet ket luan va danh gia tinh kha thi cua bai toan

### File phu trach

- `notebooks/01_data_collection_and_cleaning.ipynb`
- `notebooks/02_eda_and_visualization.ipynb`
- `notebooks/03_midterm_submission_final.ipynb`
- `reports/eda_salary_distribution.png`
- `reports/correlation_heatmap.png`
- `reports/skills_clustermap.png`
- `reports/tsne_visualization.png`

### Noi dung phai noi khi thuyet trinh

- Bieu do nao tra loi cau hoi nao
- Bien nao co anh huong den salary
- Du lieu co bieu hien xu huong/cum hay khong
- Bai toan co kha thi de model hoa hay khong

### Phan phai viet trong notebook tong

- `4. Mo ta du lieu ban dau`
- `5. Thong ke mo ta va truc quan hoa don bien`
- `9. Truc quan hoa moi quan he da bien`
- `10. Truc quan hoa khong gian du lieu nhieu chieu`
- `11. Danh gia tinh kha thi cua bai toan`
- `12. Ket luan`
- `13. Tai lieu tham khao`

## Cach ghep bai nop

1. Thanh vien 1 nop du lieu tho va mo ta nguon du lieu.
2. Thanh vien 2 nop du lieu sau cleaning va mo ta tien xu ly.
3. Thanh vien 3 tong hop notebook cuoi cung, nhan xet va ket luan.
4. Ca nhom cung doc lai `README.md` va checklist truoc khi nop.

## Phan notebook tong nen chia theo nguoi

- Thanh vien 1 viet phan mo ta bai toan lien quan den du lieu crawl va toan bo muc thu thap du lieu.
- Thanh vien 2 viet phan cleaning, encoding, NLP va feature engineering.
- Thanh vien 3 viet phan EDA, truc quan hoa da bien, t-SNE, ket luan va tai lieu tham khao.
- Ca nhom cung ra soat phan `1. Phat bieu bai toan`, vi day la phan mo dau quan trong nhat cua notebook.

## Checklist nhanh cho tung nguoi

### Thanh vien 1

- Co raw data
- Co so mau > 1000
- Co mo ta cach crawl

### Thanh vien 2

- Co clean data
- Co cleaning truoc/sau
- Co encoding hoac NLP

### Thanh vien 3

- Co bieu do mo ta
- Co nhan xet
- Co ket luan va tai lieu tham khao
