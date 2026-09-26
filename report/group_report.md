# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4-L3B              |
| Tên nhóm         | O4     |
| Repository         | https://github.com/kascenite/K4-L3B-Day10-O4-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-26               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Thành Vinh | 2A202602889 | Baseline Pipeline Integrator & Reporting | `phase1.py`, `reporting.py`, `embeddings.py`, `index.py`, `qa.py`; baseline metrics/report |
| 2 | Lương Sỹ Khánh | 2A202602715 | Data Foundation & Recovery + Quality Gate | `crossref.py`, `cleaning.py`, `quality.py`, sửa đọc CSV trong `corruption_flow.py`; `data/raw/`, `data/clean/`, `data/quality/` |
| 3 | Trần Nam Anh | 2A202602901 | Benchmark Evaluation & Vector Store Indexing | `testset.py`, `embeddings.py`; `data/eval/test_set.json`, collection `papers-baseline` |
| 4 | Nguyễn Thành Nam | 2A202602827 | Synthetic Data Corruption Suite & đo lường suy giảm RAG | `corruption.py`, `corruption_flow.py`, `reporting.py` (báo cáo corruption), sửa `qa.py`; `corruption_log.json`, `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` |

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**

Nhóm hoàn thành CP0 đến CP5. Pipeline lấy 24 bài báo tiếng Anh từ Crossref API, làm sạch, kiểm tra bằng Great Expectations 1.x, index vào ChromaDB bằng `all-MiniLM-L6-v2` và đánh giá trên 10 câu hỏi thuộc 4 nhóm (summary, authors, date, categories).

Baseline tạo đủ artifact: raw response và raw records, bảng sạch CSV/JSON, collection `papers-baseline` 24 tài liệu, `test_set.json`, `baseline_metrics.json` và `phase1_report.md`. Baseline đạt hit rate 1.00 và token F1 1.00.

Corruption tiêm 6 loại lỗi. Ảnh hưởng rõ nhất là xóa 4 bài mới nhất: 5/10 câu hỏi nhắm vào các bài này nên mất tài liệu đúng, hit rate giảm còn 0.50 và token F1 còn 0.72. Quality gate phát hiện lỗi với 3 expectation fail (số dòng, `paper_id` trùng, summary rỗng).

Repair dựng lại dữ liệu từ `crossref_records.json`. Gate pass 6/6, hit rate và token F1 trở về 1.00, bằng baseline.

Giới hạn còn lại: judge chạy bằng heuristic dự phòng vì LLM evaluator không gọi được; freshness không báo động ở trạng thái corrupted vì chỉ 9% bài bị làm cũ; dữ liệu Crossref thật không có `subject` nên câu hỏi `categories` chỉ kiểm được câu "không có danh mục".

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API (fallback: snapshot) | Fetch, retry 429/5xx, parse, lọc bản ghi lỗi và tiêu đề ngoại ngữ | `data/raw/` | Lương Sỹ Khánh |
| Cleaning          | `crossref_records.json` | Bỏ JATS tag, dedupe `paper_id`, tính `age_days`, sinh `text_for_embedding` | `data/clean/` | Lương Sỹ Khánh |
| Embedding/index   | `papers_clean.json` | `all-MiniLM-L6-v2` trên CPU, Chroma cosine, 1 collection cho mỗi trạng thái | `data/chroma/`, `data/embeddings/` | Trần Nam Anh, Nguyễn Thành Vinh |
| Evaluation        | Test set 10 câu và collection baseline        | Retrieval `top_k=4`, token F1, retrieval hit, judge fallback | `data/results/baseline_metrics.json`, `baseline_answers.json`, `data/reports/phase1_report.md` | Nguyễn Thành Vinh |
| Observability     | DataFrame sạch | GX 1.x (4 expectation) và freshness SLA | `data/quality/` | Lương Sỹ Khánh (quality gate); Nguyễn Thành Vinh, Nguyễn Thành Nam (reporting) |
| Corruption/repair | Clean dataset, test set và baseline metrics        | 6 loại lỗi có seed cố định; repair bằng cleaning lại từ raw | `corruption_log.json`, `corrupted_metrics.json` | Nguyễn Thành Nam |
| Orchestration     | Raw records | `run_phase1.py` rồi `run_corruption_flow.py` | `data/reports/`, `data/results/` | Nguyễn Thành Vinh (phase 1), Nguyễn Thành Nam (corruption flow) |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `custom`            |
| `LLM_MODEL`                | `gemini-flash-lite` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 (lấy 48, giữ 24) |
| Retrieval`top_k`           | 4                   |
| Freshness threshold          | 180 ngày, tối đa 25% bài quá hạn |
| Random seed, nếu có        | 41 đến 45 (mỗi loại lỗi một seed) |

### Lệnh cài đặt

```bash
uv sync --frozen
cp .env.example .env
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | 2026-09-26 | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow   | Thành công | 2026-09-26 12:04 | `data/reports/corruption_report.md`, `data/results/corrupted_metrics.json`, `repaired_metrics.json` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | `https://api.crossref.org/works` |
| Query/filter                | `agentic retrieval augmented generation large language model`; `from-pub-date:2026-03-30,has-abstract:true`; 48 rows |
| Thời điểm lấy dữ liệu | 2026-09-26 10:06 (+07) |
| Số record nhận được    | 48 bản ghi, giữ 24 |
| Cơ chế retry/backoff      | Thử lại tối đa 3 lần khi gặp 429/5xx, chờ `Retry-After` hoặc `2^n` giây. Lỗi mạng thì đọc snapshot. |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| `paper_id` | str | Có | DOI viết thường | Thiếu thì loại, trùng thì giữ bản đầu |
| `title` | str | Có | Tiêu đề | Thiếu hoặc ngoại ngữ thì loại |
| `summary` | str | Có | Abstract đã bỏ tag | Dưới 50 ký tự thì loại |
| `published` | str `YYYY-MM-DD` | Có | Ngày xuất bản | Sai định dạng thì loại |
| `authors`, `categories` | list[str] | Không | Tác giả, chủ đề | Để rỗng, ghi `Unknown` trong text |
| `age_days` | int | Có | Số ngày từ `published` tới ngày chạy | Tính khi cleaning |
| `text_for_embedding` | str | Có | Text đưa vào embedding | Tính khi cleaning |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Loại bản ghi thiếu DOI/title/abstract | Completeness | 0/48 | `crossref_response.json` |
| Loại tiêu đề ngoại ngữ | Validity | 3/48 (1 Nga, 2 Indonesia) | So raw với `crossref_records.json` |
| Bỏ JATS tag trong abstract | Validity | 40/48 | Không còn `<jats:` trong `text_for_embedding` |
| Bỏ chữ "Abstract" thừa đầu summary | Accuracy | 10/24 | So summary trước và sau cleaning |
| Dedupe theo `paper_id` | Uniqueness | 0/24 | GX unique pass |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

`paper_id` là DOI viết thường. DOI không đổi giữa các lần crawl nên dùng được làm `ground_truth_doc_ids` cho cả 3 trạng thái. `age_days` bằng ngày chạy trừ `published` (hiện từ 11 đến 178 ngày). `text_for_embedding` có 5 dòng: `Title`, `Authors`, `Published`, `Categories`, `Summary`; trường rỗng ghi `Unknown`.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 10 |
| Các `question_type`                    | `summary`, `authors`, `date`, `categories` |
| Ground-truth document ID                 | `paper_id` của record được chọn, lưu trong `ground_truth_doc_ids` |
| Embedding model                          | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector store/collection                  | ChromaDB collection `papers-baseline`, cosine space, 24 documents |
| Retrieval `top_k`                       | 4 |
| LLM provider/model                       | `custom` / `gemini-flash-lite`; judge fallback trong lần chạy baseline |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

Giữ nguyên test set và `ground_truth_doc_ids` giúp các thay đổi metric giữa baseline, corrupted và repaired chỉ phản ánh thay đổi dữ liệu/index. Nếu thay câu hỏi hoặc ground truth giữa các trạng thái, độ khó benchmark trở thành biến gây nhiễu và phép so sánh không còn công bằng.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | 24 parsed records |
| Cleaned dataset          | `data/clean/`                        | Có | 24 clean rows trong CSV và JSON |
| Embedding manifest/index | `data/embeddings/`, `data/chroma/`   | Có | Portable manifest; collection có 24 documents |
| Evaluation set           | `data/eval/`                         | Có | 10 câu, đủ 4 question types |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có | Hit rate và token F1 đã xác minh |
| Quality/freshness        | `data/quality/`                      | Có | 6/6 expectations pass; freshness pass |
| Baseline report          | `data/reports/phase1_report.md`      | Có | Được sinh tự động từ artifacts |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` | 1.0000 | 10/10 câu lấy được ground-truth document |
| `mean_token_f1`      | 1.0000 | Câu trả lời khớp ground truth theo token F1 |
| `judge_accuracy`     | 1.0000 | Heuristic fallback đánh giá đúng 10/10; chưa phải live LLM judge |
| `mean_judge_score`   | 5.00 | Điểm fallback judge trung bình tối đa |
| Ragas, nếu có        | N/A | Mặc định bỏ qua; đặt `RUN_RAGAS=1` để chạy pass chậm hơn |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| Row count | Completeness | 24–24 rows | Pass: 24 | `data/quality/baseline_quality_report.json` |
| `paper_id` not null và unique | Completeness/Uniqueness | 0 null, 0 duplicate | Pass | `data/quality/baseline_quality_report.json` |
| `title` not null | Completeness | 0 null | Pass | `data/quality/baseline_quality_report.json` |
| Summary length | Validity | 50–10,000 ký tự | Pass | `data/quality/baseline_quality_report.json` |
| `age_days` trong SLA | Freshness | Ít nhất 75% ≤ 180 ngày | Pass | `data/quality/baseline_quality_report.json` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Clean dataframe; `data/quality/freshness_report.json` |
| Timestamp mới nhất       | 2026-09-15 |
| Ngưỡng freshness         | 180 ngày; stale ratio tối đa 25% |
| Trạng thái baseline      | Fresh |
| Lý do                     | 0/24 records quá 180 ngày; stale ratio 0% |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| Drop latest records | Xóa 20% bài mới nhất | 4 | Row count fail | Row count 22, fail; 5/10 câu mất tài liệu đúng | Cleaning lại từ raw |
| Blank summary | Xóa rỗng summary | 2 | Độ dài summary fail | Expectation summary fail | Cleaning lại từ raw |
| Inject noise | Thêm ` #@! NOISE_DATA !@#` vào summary | 2 | Không có expectation riêng | Không làm đổi metric | Cleaning lại từ raw |
| Truncate title | Cắt title còn 7 ký tự | 2 | Không có expectation riêng | Không làm đổi metric | Cleaning lại từ raw |
| Stale date | Lùi `published` 365 ngày | 2 | Freshness | 2/22 stale (9%), dưới ngưỡng 25%, vẫn Fresh | Cleaning lại từ raw |
| Duplicate rows | Nhân đôi dòng | 2 | Unique `paper_id` fail | Expectation unique fail | Cleaning lại từ raw (dedupe) |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: log ghi đủ 6 loại lỗi, số record và index bị tác động. Seed nằm trong `corruption.py` (41 đến 45).

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

Repair không sửa từng dòng lỗi. Nó đọc lại `crossref_records.json` (raw snapshot đã commit) và chạy lại `build_clean_dataframe`. Vì vậy kết quả không phụ thuộc vào dữ liệu hỏng, và chạy lại bao nhiêu lần cũng ra cùng 24 dòng. Bảng repaired khớp với bảng sạch baseline ở các cột nội dung.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      1.00 |       0.50 |      1.00 |                      -0.50 |             100% | 5 câu hỏi về bài bị xóa |
| `mean_token_f1`        |      1.00 |       0.72 |      1.00 |                      -0.28 |             100% | 2 câu `categories` vẫn đúng |
| `judge_accuracy`       |      1.00 |       0.70 |      1.00 |                      -0.30 |             100% | Judge heuristic |
| `mean_judge_score`     |      5.0 |       3.8 |      5.0 |                      -1.2 |             100% | Judge heuristic |
| Quality checks pass/fail |      Pass 6/6 |       Fail 3/6 |      Pass 6/6 |                      3 fail |             100% | Row count, unique, summary |
| Freshness status         |      Fresh |       Fresh |      Fresh |                      2/22 stale |             0 stale | Dưới ngưỡng 25% |

1. Xóa 4 bài mới nhất và nhân đôi 2 dòng → gate fail ở row count và unique `paper_id` → hit rate giảm từ 1.00 xuống 0.50 vì 5/10 câu hỏi nhắm vào 4 bài bị xóa.
2. Repair cleaning lại từ raw snapshot → gate pass 6/6 với 24 dòng → hit rate, token F1 và judge trở về bằng baseline.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Pipeline lỗi `WinError 10013` khi Sentence Transformers gửi HEAD request tới Hugging Face dù model đã cache; QA baseline cũng không exact-match được tiêu đề trong dấu ngoặc cong `‘…’` của câu hỏi tiếng Việt.
- **Nguyên nhân:** Model loader mặc định vẫn kiểm tra metadata online; QA parser ban đầu chỉ nhận dấu nháy và keyword tiếng Anh.
- **Cách xử lý:** Ưu tiên `local_files_only=True` trước khi fallback online; hỗ trợ dấu ngoặc thẳng/cong và bốn loại câu hỏi tiếng Việt; tái sử dụng Chroma collection thay vì delete/recreate để tránh segment mồ côi.
- **Cách xác minh:** Chạy lại `python script/run_phase1.py` khi network bị chặn; pipeline exit code 0, Chroma count 24, `retrieval_hit_rate=1.0`, `mean_token_f1=1.0` trong `data/results/baseline_metrics.json`.

Vấn đề thứ hai, ở corruption flow:

- **Triệu chứng:** `run_corruption_flow.py` crash ở bước đánh giá corrupted với `KeyError: 'categories_joined'` trong `src/retrieval/qa.py`.
- **Nguyên nhân:** corruption flow đọc lại `papers_clean.csv` bằng `pd.read_csv`. Ô `categories_joined` rỗng (cả 24 bài không có `subject`) bị đọc thành `NaN`, Chroma bỏ key này khỏi metadata, và `qa.py` truy cập key bằng `[]`.
- **Cách xử lý:** `qa.py` đổi sang `metadata.get(...)` (Nguyễn Thành Nam); `corruption_flow.py` đọc CSV với `keep_default_na=False` để giữ chuỗi rỗng (Lương Sỹ Khánh).
- **Cách xác minh:** `python script/run_corruption_flow.py` chạy hết và in bảng 3 trạng thái; `data/reports/corruption_report.md` được tạo.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Cả 24 bài không có `subject` | Câu hỏi nhóm `categories` thiếu đáp án | Lấy chủ đề từ trường khác hoặc bỏ nhóm câu hỏi này |
| Lọc ngôn ngữ bằng heuristic | Tiêu đề ngoại ngữ viết chữ Latin có thể lọt qua | Dùng bộ nhận diện ngôn ngữ, đo số bản ghi phân loại sai |
| Crossref là nguồn sống | Mỗi lần crawl ra tập bài khác | Repair và đánh giá từ raw snapshot đã commit, không crawl lại |
| Judge chạy bằng heuristic dự phòng | `judge_accuracy` chỉ phản ánh token F1 | Cấu hình LLM evaluator chạy được, so số câu judge LLM và heuristic cho kết quả khác nhau |
| Freshness không báo động ở trạng thái corrupted | Lỗi ngày cũ không bị phát hiện | Lùi ngày cho hơn 25% số bài, kiểm tra `is_fresh = false` |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
