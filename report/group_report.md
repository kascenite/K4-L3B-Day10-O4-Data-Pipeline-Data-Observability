# Group Report — Day 10: Data Pipeline & Data Observability

> Đã xong CP0 và CP1. Ô `[Chờ CPx]` sẽ điền từ artifact thật khi chạy xong checkpoint đó.

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
| 1 | [Họ tên] | [MSSV] | [Vai trò] | [File, hàm hoặc artifact] |
| 2 | Lương Sỹ Khánh | 2A202602715 | Data Foundation & Recovery + Quality Gate | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/observability/quality.py`; `data/raw/`, `data/clean/`, `data/quality/` |
| 3 | [Họ tên] | [MSSV] | [Vai trò] | [File, hàm hoặc artifact] |
| 4 | Nguyễn Thành Nam | 2A202602827 | [Synthetic Data Corruption Suite & đo lường suy giảm RAG] | `src/ingestion/corruption.py`, `corruption_log.json`, `corrupted_metrics.json` |

## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

[Viết phần tóm tắt tại đây.]

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

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
| Embedding/index   | [Input]        | [Model/index config]       | [Đường dẫn artifact] | [Thành viên] |
| Evaluation        | [Input]        | [Test set và metrics]     | [Đường dẫn artifact] | [Thành viên] |
| Observability     | DataFrame sạch | GX 1.x (4 expectation) và freshness SLA | `data/quality/` | Lương Sỹ Khánh (quality gate); [Thành viên] (reporting) |
| Corruption/repair | [Input]        | [Corruption và repair]    | [Đường dẫn artifact] | [Thành viên] |
| Orchestration     | [Input]        | [Thứ tự chạy]           | [Reports/metrics]        | [Thành viên] |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | `openrouter`        |
| `LLM_MODEL`                | `google/gemini-2.5-flash` |
| Embedding model              | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 (lấy 48, giữ 24) |
| Retrieval`top_k`           | 4                   |
| Freshness threshold          | 180 ngày, tối đa 25% bài quá hạn |
| Random seed, nếu có        | [Chờ CP4] |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

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
| Baseline pipeline | [Thành công/Thất bại một phần/Thất bại] | [Thời gian]                  | [Artifact hoặc log đã che secret] |
| Corruption flow   | [Thành công/Thất bại một phần/Thất bại] | [Thời gian]                  | [Artifact hoặc log đã che secret] |

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
| Số câu hỏi                            | [Số lượng]                 |
| Các`question_type`                    | [Danh sách]                  |
| Ground-truth document ID                 | [Cách tạo/đối chiếu]     |
| Embedding model                          | [Tên model]                  |
| Vector store/collection                  | [Tên/config]                 |
| Retrieval`top_k`                       | [Giá trị]                   |
| LLM provider/model                       | [Giá trị]                   |
| Test set dùng chung cho ba trạng thái | [Đường dẫn hoặc ID/hash] |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

[Giải thích tại đây.]

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có | 48 bản ghi thô, 24 record |
| Cleaned dataset          | `data/clean/`                        | Có | 24 dòng, 16 cột |
| Embedding manifest/index | `data/embeddings/`                   | [Có/Thiếu] | [Ghi chú] |
| Evaluation set           | `data/eval/`                         | [Có/Thiếu] | [Ghi chú] |
| Baseline metrics         | `data/results/baseline_metrics.json` | [Có/Thiếu] | [Ghi chú] |
| Quality/freshness        | `data/quality/`                      | Có | Bản chạy CP1 (`test_*`), bản baseline chờ CP3 |
| Baseline report          | `data/reports/phase1_report.md`      | [Có/Thiếu] | [Ghi chú] |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     [Giá trị] | [Ý nghĩa trong kết quả của nhóm]  |
| `mean_token_f1`      |     [Giá trị] | [Diễn giải]                           |
| `judge_accuracy`     |     [Giá trị] | [Diễn giải]                           |
| `mean_judge_score`   |     [Giá trị] | [Diễn giải]                           |
| Ragas, nếu có        | [Giá trị/N/A] | [Diễn giải hoặc lý do không chạy] |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| `expect_table_row_count_to_be_between` | Completeness | đúng 24 dòng | Pass (24) | `data/quality/test_quality_report.json` |
| `expect_column_values_to_not_be_null` (`paper_id`) | Completeness | 0 null | Pass (0) | như trên |
| `expect_column_values_to_be_unique` (`paper_id`) | Uniqueness | 0 trùng | Pass (0) | như trên |
| `expect_column_values_to_not_be_null` (`title`) | Completeness | 0 null | Pass (0) | như trên |
| `expect_column_value_lengths_to_be_between` (`summary`) | Validity | 50 đến 10000 ký tự | Pass (0 vi phạm) | như trên |
| `expect_column_values_to_be_between` (`age_days`, `mostly=0.75`) | Timeliness | 0 đến 180 ngày cho ít nhất 75% dòng | Pass (0 vi phạm) | như trên |

Số liệu trên từ lệnh kiểm tra CP1. Bản baseline chính thức sẽ do `run_phase1.py` tạo ở CP3.

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | Clean dataset (`published`, `age_days`) |
| Timestamp mới nhất       | 2026-09-15 (cũ nhất 2026-04-01) |
| Ngưỡng freshness         | 180 ngày, tối đa 25% bài quá hạn |
| Trạng thái baseline      | Fresh                               |
| Lý do                     | 0/24 bài quá 180 ngày vì query chỉ lấy bài trong 180 ngày gần nhất (`data/quality/test_freshness.json`) |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| [Loại corruption] | [Mô tả]  |          [Số lượng] | [Kỳ vọng]              | [Artifact/metric]     | [Cách repair] |
| [Loại corruption] | [Mô tả]  |          [Số lượng] | [Kỳ vọng]              | [Artifact/metric]     | [Cách repair] |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: [Có/Thiếu]
- Nhận xét: [Log có đủ loại corruption, record bị tác động và tham số hay không?]

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

[Giải thích tại đây.]

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| `mean_token_f1`        |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| `judge_accuracy`       |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| `mean_judge_score`     |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| Quality checks pass/fail |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |
| Freshness status         |      [ ] |       [ ] |      [ ] |                      [ ] |             [ ] | [Nhận xét] |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. [Corruption/data change] → [quality/freshness signal] → [retrieval/answer metric].
2. [Repair action] → [quality/freshness recovery] → [agent metric recovery hoặc lý do chưa recovery].

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** [Lỗi hoặc kết quả sai.]
- **Nguyên nhân:** [Root cause.]
- **Cách xử lý:** [Thay đổi đã thực hiện.]
- **Cách xác minh:** [Lệnh và artifact.]

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Cả 24 bài không có `subject` | Câu hỏi nhóm `categories` thiếu đáp án | Lấy chủ đề từ trường khác hoặc bỏ nhóm câu hỏi này |
| Lọc ngôn ngữ bằng heuristic | Tiêu đề ngoại ngữ viết chữ Latin có thể lọt qua | Dùng bộ nhận diện ngôn ngữ, đo số bản ghi phân loại sai |
| Crossref là nguồn sống | Mỗi lần crawl ra tập bài khác | Repair và đánh giá từ raw snapshot đã commit, không crawl lại |

## 13. Checklist trước khi nộp

- [ ] Thông tin nhóm và repository chính xác.
- [ ] Phân công khớp với module, artifact và kết quả thực tế.
- [ ] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [ ] Baseline, corrupted và repaired dùng cùng evaluation set.
- [ ] Bảng metrics khớp với các file trong `data/results/`.
- [ ] Quality/freshness conclusions khớp với `data/quality/`.
- [ ] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [ ] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
