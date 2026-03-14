# Phan cong cong viec trong nhom

Tai lieu nay dung de nop kem hoac dua vao slide/notebook de mo ta ro ai phu trach phan nao trong du an.

## Tong quan de tai

De tai: Phan tich va du bao xu huong tuyen dung IT tai Viet Nam.

Muc tieu giai doan giua ky:

- Thu thap du lieu tu crawl tu cac nen tang tuyen dung.
- Lam sach, chuan hoa, ma hoa du lieu.
- Phan tich mo ta va truc quan hoa de danh gia tinh kha thi cua bai toan.
- Chua di sau vao modeling, chi danh gia kha nang xay dung mo hinh cho bai tap sau.

## Thanh vien 1 - Data Engineer

### Nhiem vu chinh

- Thiet ke crawler cho ITViec, TopCV, TopDev.
- Xu ly pagination, delay request, retry va ghi log crawl.
- Thu thap toi thieu 1000 mau du lieu tuyen dung do nhom tu crawl.
- Hop nhat du lieu ve mot schema thong nhat.

### Dau ra can nop

- Source code crawler.
- Thu muc `data/raw/` chua du lieu tho tu crawl.
- File tong hop nguon crawl, so trang da quet, so mau thu duoc theo tung website.
- Mo ta cach thu thap du lieu de dua vao notebook/slide.

### Tieu chi hoan thanh

- Du lieu la do nhom tu crawl, khong su dung dataset tai san.
- Moi ban ghi co it nhat 5 bien quan trong.
- Co dan nguon va URL crawl ro rang.

## Thanh vien 2 - Data Processor va NLP Specialist

### Nhiem vu chinh

- Kiem tra schema va hop nhat ten cot.
- Xu ly gia tri thieu, trung lap, format luong, format dia diem, level, kinh nghiem.
- Chuan hoa salary ve cung don vi de tao `salary_avg`.
- Trich xuat ky nang tu tieu de va mo ta cong viec.
- Ma hoa du lieu danh muc va tao bien dac trung.

### Dau ra can nop

- File `data/interim/` sau hop nhat.
- File `data/processed/` sau cleaning va feature engineering.
- Mo ta ro quy trinh cleaning truoc/sau.
- Cac cot dac trung moi nhu `experience_years`, `salary_avg`, `skills_extracted`, cac cot dummy skill.

### Tieu chi hoan thanh

- Co mo ta cach xu ly du lieu nhieu, null, trung lap va salary khong ro rang.
- Co minh hoa phan bo du lieu truoc va sau cleaning.
- Co ma hoa hoac vector hoa cho bien category/text.

## Thanh vien 3 - Data Analyst va Visualizer

### Nhiem vu chinh

- Thuc hien EDA don bien va da bien.
- Tao cac bieu do phan bo luong, top ky nang, salary theo level, location, company type.
- Ve correlation map, scatter plot, box plot, distribution plot, clustermap.
- Truc quan hoa du lieu nhieu chieu bang t-SNE neu du lieu da duoc vector hoa.
- Viet nhan xet va ket luan ve tinh kha thi cua bai toan.

### Dau ra can nop

- Cac bieu do dua vao notebook/slide.
- Cac nhan xet sau moi phan tich.
- Phan ket luan tong hop.
- Phan tai lieu tham khao o cuoi notebook/slide.

### Tieu chi hoan thanh

- Moi bieu do phai tra loi mot cau hoi cu the.
- Phan ket luan phai noi ro bai toan co kha thi hay khong.
- Chi ra nhom dac trung co gia tri de xay dung mo hinh trong bai tap sau.

## Cach ghep phan nop thanh mot notebook thong nhat

1. Thanh vien 1 cung cap thong tin nguon du lieu va quy trinh crawl.
2. Thanh vien 2 chen quy trinh cleaning, encoding, feature engineering.
3. Thanh vien 3 chen EDA, da bien, t-SNE, ket luan.
4. Ca nhom ra soat de dam bao notebook co day du cac muc bat buoc va ngon ngu thong nhat.

## Checklist truoc khi nop

- Co phat bieu bai toan o dau notebook.
- Co noi ro `Y = salary_avg` va day la bai toan hoi quy.
- Co lap luan tinh kha thi ve du lieu.
- Co mo ta nguon du lieu va cach nhom tu crawl.
- So mau lon hon 1000.
- So bien lon hon hoac bang 5.
- Co thong ke mo ta don bien.
- Co cleaning va minh hoa truoc/sau cleaning.
- Co encoding hoac vector hoa text.
- Co feature engineering.
- Co truc quan hoa da bien hoac t-SNE/clustering observation.
- Co ket luan.
- Co tai lieu tham khao o cuoi notebook.
