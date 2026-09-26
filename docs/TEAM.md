# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `O4`
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-Day10-O4-Data-Pipeline-Data-Observability`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Nguyễn Thành Vinh | 2A202602889 | | Baseline Pipeline Integrator & Reporting (`phase1.py`, `reporting.py`, `qa.py`, `index.py`, `embeddings.py`) | `report/Nguyễn Thành Vinh_individual_report.md` |
| 2 | Lương Sỹ Khánh | 2A202602715 | | Data Foundation & Recovery (`crossref.py`, `cleaning.py`, raw data) + GX Quality Gate (`quality.py`) | `report/individual_2A202602715_LuongSyKhanh.md` |
| 3 | Trần Nam Anh | 2A202602901 | | Benchmark Evaluation & Vector Store Indexing (`testset.py`, `embeddings.py`, collection `papers-baseline`) | `report/TranNamAnh-2A202602901.md` |
| 4 | Nguyễn Thành Nam | 2A202602827 | | Synthetic Data Corruption Suite & đo lường suy giảm RAG (`corruption.py`, `corruption_flow.py`, báo cáo corruption) | `report/individual_report_2A202602827_Nguyễn_Thành_Nam.md` |

---

## # Cá nhân

### ## Nguyễn Thành Vinh - 2A202602889
- **Vai trò:** Tích hợp baseline pipeline & báo cáo pha 1.
- **Công việc chi tiết đã hoàn thành:**
  - Kết nối luồng baseline trong `src/pipelines/phase1.py`: cleaning, quality gate, index, evaluation, kiểm tra số dòng và số tài liệu trong Chroma (CP3).
  - Sinh báo cáo `data/reports/phase1_report.md` bằng `generate_phase1_report` trong `src/observability/reporting.py`.
  - Cho `qa.py` nhận câu hỏi tiếng Việt và dấu ngoặc cong; cho model embedding chạy offline khi đã có cache (`embeddings.py`, `index.py`).
- **Điều học được / Đóng góp chính:**
  - Orchestration cần invariant rõ ràng (row count, Chroma count) và phải chạy lặp lại được mà không sinh trạng thái thừa.

### ## Lương Sỹ Khánh - 2A202602715
- **Vai trò:** Phụ trách Ingestion, Làm sạch dữ liệu & Quality Gate.
- **Công việc chi tiết đã hoàn thành:**
  - Thu thập Crossref API trong `src/ingestion/crossref.py`: retry khi gặp 429/5xx, fallback đọc snapshot local, lọc bản ghi lỗi và tiêu đề không phải tiếng Anh, lưu 2 file raw (CP0).
  - Làm sạch dữ liệu trong `src/ingestion/cleaning.py`: bỏ JATS tag, dedupe theo `paper_id`, tính `age_days`, sinh `text_for_embedding` 5 phần (CP1).
  - Quality Gate GX 1.x và Freshness SLA trong `src/observability/quality.py` (CP1).
  - Sửa lỗi `KeyError: 'categories_joined'` trong `src/pipelines/corruption_flow.py` bằng cách giữ chuỗi rỗng khi đọc lại CSV (CP5).
- **Điều học được / Đóng góp chính:**
  - Truy vết nguồn gốc dữ liệu (Data Lineage): lưu raw snapshot trước khi biến đổi để repair luôn chạy lại được.

### ## Trần Nam Anh - 2A202602901
- **Vai trò:** Phụ trách Benchmark Evaluation & Vector Store Indexing.
- **Công việc chi tiết đã hoàn thành:**
  - Sinh bộ 10 câu hỏi qua 4 nhóm (summary, authors, date, categories) trong `src/evaluation/testset.py`, lưu `data/eval/test_set.json` (CP2).
  - Triển khai embedding `sentence-transformers/all-MiniLM-L6-v2` trong `src/retrieval/embeddings.py`.
  - Nạp 24 tài liệu sạch vào ChromaDB collection `papers-baseline` (CP2).
- **Điều học được / Đóng góp chính:**
  - RAG agent rất nhạy với chất lượng dữ liệu: metadata lỗi hay text nhiễu không làm crash nhưng làm giảm chất lượng câu trả lời.

### ## Nguyễn Thành Nam - 2A202602827
- **Vai trò:** Phụ trách Data Corruption & đo lường suy giảm RAG.
- **Công việc chi tiết đã hoàn thành:**
  - Tiêm 6 kịch bản lỗi có seed cố định trong `src/ingestion/corruption.py` và ghi `data/results/corruption_log.json` (CP4).
  - Tích hợp luồng corruption, repair và đánh giá lại trong `src/pipelines/corruption_flow.py`; xuất `corrupted_metrics.json`, `repaired_metrics.json` (CP4, CP5).
  - Sinh báo cáo đối chiếu 3 trạng thái `data/reports/corruption_report.md` (`reporting.py`); sửa `qa.py` để không crash khi thiếu metadata.
- **Điều học được / Đóng góp chính:**
  - Quality Gate và Freshness SLA kiểm tra hai vấn đề khác nhau, nên cần xem cả hai khi đánh giá chất lượng dữ liệu.
