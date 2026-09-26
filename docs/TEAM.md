# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `O4`
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-Day10-O4-Data-Pipeline-Data-Observability`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | | | | Pipeline Integrator (`core/`, `phase1.py`, `corruption_flow.py`) | `report/.md` |
| 2 | Lương Sỹ Khánh | 2A202602715 | | Data Foundation & Recovery (`crossref.py`, `cleaning.py`, raw data) + GX Quality Gate (`quality.py`) | `report/individual_2A202602715_LuongSyKhanh.md` |
| 3 | | | | RAG & Vector Index (`retrieval/index.py`, `embeddings.py`, ChromaDB) | `report/<MSSV3>_HoTen.md` |
| 4 | | | | Observability & Evaluation (`quality.py` GX 1.x, `testset.py`, reporting) | `report/<MSSV4>_HoTen.md` |

*(Nếu nhóm có 3 hoặc 5-6 thành viên, xem bảng phân công chi tiết theo vai trò trong file `CHECKPOINTS.md`)*.

---

## # Cá nhân

### ## HoVaTen1-MSSV1
- **Vai trò:** Trưởng nhóm & Điều phối Pipeline.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập cấu hình hệ thống `core/config.py` và đường dẫn artifacts `core/utils.py`.
  - Kết nối luồng thực thi trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
  - Kiểm tra tính nhất quán của các artifacts và theo dõi Contributor tracking trên GitHub nhánh `main`.
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu sắc về thiết kế Idempotent Pipeline và quản lý trạng thái luồng dữ liệu đa tầng.

### ## Lương Sỹ Khánh - 2A202602715
- **Vai trò:** Phụ trách Ingestion, Làm sạch & Phục hồi dữ liệu; Quality Gate.
- **Công việc chi tiết đã hoàn thành:**
  - Thu thập Crossref API trong `src/ingestion/crossref.py`: retry khi gặp 429/5xx, fallback đọc snapshot local, lọc bản ghi lỗi và tiêu đề không phải tiếng Anh, lưu 2 file raw (CP0).
  - Làm sạch dữ liệu trong `src/ingestion/cleaning.py`: bỏ JATS tag, dedupe theo `paper_id`, tính `age_days`, sinh `text_for_embedding` 5 phần (CP1).
  - Quality Gate GX 1.x và Freshness SLA trong `src/observability/quality.py` (CP1).
  - Đang làm: Idempotent Repair từ raw snapshot (CP5).
- **Điều học được / Đóng góp chính:**
  - Truy vết nguồn gốc dữ liệu (Data Lineage): lưu raw snapshot trước khi biến đổi để repair luôn chạy lại được.

### ## HoVaTen3-MSSV3
- **Vai trò:** Phụ trách RAG, Vector Database & Embedding.
- **Công việc chi tiết đã hoàn thành:**
  - Quản lý mô hình embedding `sentence-transformers/all-MiniLM-L6-v2`.
  - Nạp và quản lý 3 collection riêng biệt trong ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
  - Xây dựng QA Agent truy vấn ngữ cảnh chính xác theo tài liệu.
- **Điều học được / Đóng góp chính:**
  - Cách cô lập các không gian vector để so sánh khách quan giữa dữ liệu sạch và dữ liệu bị lỗi.

### ## HoVaTen4-MSSV4
- **Vai trò:** Phụ trách Data Observability & Benchmark Evaluation.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập Quality Gate theo chuẩn mới **Great Expectations 1.x** và giám sát Freshness SLA trong `src/observability/quality.py`.
  - Xây dựng bộ câu hỏi đánh giá chuẩn trong `src/evaluation/testset.py`.
  - Đo lường và xuất bảng đối chiếu 3 trạng thái vào `data/reports/corruption_report.md`.
- **Điều học được / Đóng góp chính:**
  - Cách thiết lập hệ thống cảnh báo sớm chặn đứng hiện tượng Silent Failure trước khi dữ liệu vào serving layer.
