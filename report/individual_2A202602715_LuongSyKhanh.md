# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Lương Sỹ Khánh             |
| MSSV               | 2A202602715                |
| Khóa/Lớp         | K4-L3B                     |
| Tên nhóm         | O4                         |
| Vai trò chính    | Data Foundation & Recovery, Quality Gate |
| Repository         | https://github.com/kascenite/K4-L3B-Day10-O4-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-26                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------- |
| Raw ingestion | `crossref.py`: `fetch_source_records`, `parse_crossref_payload`, `load_raw_records` | Crossref API, `Settings` | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành |
| Cleaning | `cleaning.py`: `build_clean_dataframe` | 24 `PaperRecord` | `data/clean/papers_clean.csv`, `.json` | Hoàn thành |
| Quality gate | `quality.py`: `run_data_quality_checks`, `build_freshness_report` | DataFrame sạch | `data/quality/<name>_quality_report.json`, `<name>_freshness.json` | Hoàn thành |
| Repair | Hàm repair cho `corruption_flow.py` | `data/raw/crossref_records.json` | Repaired dataset | Chưa hoàn thành (CP5) |

Test set (`testset.py`) và ChromaDB index (`index.py`) đọc trực tiếp `papers_clean.json` do tôi tạo.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ------------------------------ | ------- |
| Cài môi trường `uv` và `.env` | Cả nhóm | `.venv` Python 3.12 in `Môi trường sẵn sàng` |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Tải Crossref có retry và fallback | `crossref.py` | 24 bài, 2 file raw | Lệnh CP0: `Đã tải 24 bài báo` |
| Lọc tiêu đề không phải tiếng Anh | `_is_english` | Loại 3/48 bản ghi (1 Nga, 2 Indonesia) | So `crossref_response.json` với `crossref_records.json` |
| Làm sạch, sinh `text_for_embedding` | `cleaning.py` | 24 dòng sạch | Lệnh CP1: `Clean thành công 24 dòng` |
| Quality gate GX 1.x và freshness | `quality.py` | 6/6 expectation pass, `is_fresh = true` | Lệnh CP1: `Quality check status = True` |

Output cụ thể: `data/quality/test_quality_report.json` cho 6/6 expectation pass trên 24 dòng. Tôi cũng thử gate trên dữ liệu hỏng (1 dòng trùng, 1 summary rỗng, 10/25 dòng có `age_days = 400`). Kết quả `success = False`, `is_fresh = False`, fail 4 expectation: row count, unique `paper_id`, độ dài summary, freshness.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Agent chỉ trả lời đúng khi dữ liệu đưa vào index đủ, không trùng và còn mới. Phần của tôi lấy dữ liệu từ Crossref, làm sạch và chặn dữ liệu xấu trước khi embed.

### Cách triển khai

- Ingestion: gọi `api.crossref.org/works` với filter 180 ngày gần nhất và `has-abstract:true`, lấy 48 bản ghi. Gặp HTTP 429/5xx thì thử lại tối đa 3 lần (chờ theo `Retry-After` hoặc `2^n` giây). Lỗi mạng thì đọc snapshot `crossref_response.json`.
- Parse: `paper_id` là DOI viết thường. Bỏ bản ghi thiếu DOI, title hoặc abstract, trùng DOI, hoặc tiêu đề không phải tiếng Anh. Giữ 24 bản ghi đầu.
- Cleaning: bỏ tag JATS/HTML và chữ "Abstract" thừa ở đầu tóm tắt, chuẩn hóa khoảng trắng, tính `age_days`, bỏ dòng summary dưới 50 ký tự hoặc sai ngày, dedupe theo `paper_id`.
- Quality gate: GX 1.x ephemeral context, gồm 4 expectation bắt buộc và 1 expectation freshness (`age_days` 0 đến 180 cho ít nhất 75% dòng).

### Input, output và contract

| Thành phần                   | Mô tả |
| ------------------------------ | ----- |
| Input                          | Crossref API hoặc snapshot; `Settings` trong `core/config.py` |
| Output                         | 2 file raw; bảng sạch 16 cột, `published` dạng `YYYY-MM-DD`, `age_days` kiểu int |
| Module phụ thuộc             | `core/config.py`, `core/utils.py` |
| Module sử dụng output        | `testset.py`, `index.py`, `qa.py`, `phase1.py`, `corruption_flow.py` |
| Điều kiện lỗi cần xử lý | HTTP 429/5xx, mất mạng, JATS XML trong abstract, thiếu `subject`, DOI trùng, tiêu đề ngoại ngữ |

### Cách xác minh

```bash
source .venv/bin/activate
python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"
python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print(f'Tín hiệu hoàn thành: Quality check status = {res[\"success\"]}')"
```

- **Kết quả mong đợi:** `Đã tải 24 bài báo`, `Clean thành công 24 dòng`, `Quality check status = True`.
- **Kết quả thực tế:** đúng như mong đợi (chạy 2026-09-26, dữ liệu lấy lúc 10:06).
- **Artifact/log:** `data/raw/`, `data/clean/`, `data/quality/test_quality_report.json`, `data/quality/test_freshness.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lần crawl đầu có 1 bài tiếng Nga và 2 bài tiếng Indonesia. Trường `language` của Crossref trống ở phần lớn bản ghi.
- **Các phương án đã cân nhắc:** (1) chỉ dùng trường `language`; (2) bắt buộc tiêu đề có hư từ tiếng Anh; (3) thêm thư viện `langdetect`; (4) loại tiêu đề có chữ ngoài ASCII hoặc có hư từ của ngôn ngữ Latin khác (dan, untuk, para, und...).
- **Phương án đã chọn:** (1) kết hợp (4), và lấy 48 bản ghi để sau khi lọc vẫn đủ 24.
- **Lý do:** (3) phải sửa `uv.lock` dùng chung của nhóm. (2) loại nhầm tiêu đề tiếng Anh (xem mục 6). (4) chỉ cần thư viện chuẩn. Nhược điểm: tiêu đề ngoại ngữ không chứa từ nào trong danh sách vẫn lọt qua.
- **Bằng chứng quyết định phù hợp:** trong 48 bản ghi, bộ lọc loại đúng 3 tiêu đề ngoại ngữ; 24 tiêu đề còn lại đều là tiếng Anh. Snapshot gốc vẫn parse ra đúng 24 record như ban đầu.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** sau khi thêm bộ lọc, snapshot offline chỉ còn `snapshot parse: 23`.
- **Lệnh hoặc bước tái hiện:** chạy `parse_crossref_payload` trên `git show HEAD:data/raw/crossref_response.json`.
- **Nguyên nhân gốc:** quy tắc "phải có hư từ tiếng Anh" loại tiêu đề `Synthetic Corruption Testing: Stress-Testing Vector Search Robustness` vì nó không có the/of/for/and. Khi mất mạng, fallback chỉ trả 23 bài và row count expectation sẽ fail.
- **Cách xử lý:** đảo quy tắc, chỉ loại tiêu đề có hư từ của ngôn ngữ khác.
- **Cách xác minh sau khi sửa:** snapshot parse khớp 100% với `crossref_records.json` gốc; crawl live vẫn loại đúng 3 tiêu đề và trả 24 bài.
- **Điều học được:** quy tắc lọc phải được thử trên cả dữ liệu live lẫn snapshot fallback.

## 7. Hiểu biết về luồng end-to-end

**Câu trả lời:**

1. `crossref.py` lưu payload thô rồi parse thành 24 record. `cleaning.py` chuẩn hóa và ghép `text_for_embedding`. `index.py` embed bằng `all-MiniLM-L6-v2` và lưu vào ChromaDB collection `papers-baseline` kèm metadata.
2. Mỗi câu hỏi có `ground_truth` và `ground_truth_doc_ids` (DOI). Hit rate đếm câu hỏi có doc đúng trong top-k; token F1 so câu trả lời với `ground_truth`.
3. Quality checks kiểm tra từng dòng và cả bảng (số dòng, null, trùng, độ dài). Freshness đo tuổi của cả tập (tỷ lệ bài quá 180 ngày). Dữ liệu có thể đúng schema mà vẫn cũ.
4. Giữ nguyên test set thì thay đổi metric chỉ đến từ dữ liệu, nên mới so được baseline, corrupted và repaired.
5. Repair thành công khi quality report quay lại `success = true`, `is_fresh = true`, và `repaired_metrics.json` gần bằng `baseline_metrics.json`.

## 8. Phân tích kết quả

Các ô `[Chờ CPx]` sẽ điền khi nhóm chạy xong CP2 đến CP5.

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | [Chờ CP3] | [Chờ CP4] | [Chờ CP5] | |
| `mean_token_f1`      | [Chờ CP3] | [Chờ CP4] | [Chờ CP5] | |
| `judge_accuracy`     | [Chờ CP3] | [Chờ CP4] | [Chờ CP5] | |
| `mean_judge_score`   | [Chờ CP3] | [Chờ CP4] | [Chờ CP5] | |
| Quality checks         | 6/6 pass | [Chờ CP4] | [Chờ CP5] | Thử trên dữ liệu hỏng: fail 4/6 |
| Freshness status       | Fresh (0/24 stale) | [Chờ CP4] | [Chờ CP5] | Thử với 40% dòng stale: `is_fresh = false` |

### Kết luận từ số liệu

1. [Data corruption] → [quality/freshness signal thay đổi] → [agent metric thay đổi]. [Chờ CP4]
2. [Repair action] → [quality/freshness signal phục hồi] → [agent metric phục hồi hoặc chưa phục hồi]. [Chờ CP5]

Corruption nào ảnh hưởng rõ nhất và vì sao?

[Chờ CP4]

Kết quả nào khác với kỳ vọng ban đầu?

Dữ liệu Crossref thật khác snapshot mẫu. Cả 24 bài đều không có `subject`, nên `categories_joined` rỗng và nhóm câu hỏi `categories` ở CP2 thiếu đáp án. 40/48 abstract thô có JATS XML và 16/48 bắt đầu bằng chữ "Abstract"; cleaning đã xử lý cả hai.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Lưu payload thô trước khi biến đổi thì cleaning và repair luôn chạy lại được từ cùng một nguồn.
2. Phải thử quality gate trên dữ liệu xấu. Gate chỉ từng pass trên dữ liệu tốt thì chưa chứng minh được gì.
3. Metadata thiếu hoặc text lẫn tag không làm pipeline lỗi, nhưng làm embedding và câu trả lời kém đi mà không ai thấy.

### Nếu có thêm thời gian

Thay heuristic lọc ngôn ngữ bằng bộ nhận diện ngôn ngữ thật, và thêm expectation kiểm tra `text_for_embedding` không còn `<jats:`. Đo bằng số bản ghi bị phân loại sai trên 48 bản ghi thô.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [ ] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [ ] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [ ] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Lương Sỹ Khánh
**Ngày xác nhận:** [YYYY-MM-DD]
