# Báo cáo cá nhân — Baseline Pipeline Integration & Reporting

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | **Nguyễn Thành Vinh** |
| MSSV | **2A202602889** |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | **O4** |
| Git handle | `v1rtuos024` |
| Vai trò chính | Baseline Pipeline Integrator & Reporting |
| Repository | <https://github.com/kascenite/K4-L3B-Day10-O4-Data-Pipeline-Data-Observability> |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Baseline orchestration | `src/pipelines/phase1.py`, `main()` | Raw Crossref records và cấu hình | Clean data, Chroma index, baseline metrics, quality artifacts | Hoàn thành |
| Phase 1 reporting | `src/observability/reporting.py`, `generate_phase1_report()` | Source summary, metrics, quality và freshness | `data/reports/phase1_report.md` | Hoàn thành |
| RAG benchmark compatibility | `src/retrieval/qa.py` | Câu hỏi tiếng Việt trong test set, Chroma search results | Câu trả lời theo đúng loại summary/authors/date/categories | Hoàn thành |
| Vector index robustness | `src/retrieval/embeddings.py`, `src/retrieval/index.py` | Clean dataframe và model `all-MiniLM-L6-v2` | Collection `papers-baseline` gồm 24 documents, manifest portable | Hoàn thành |

Tôi không nhận ownership cho logic tạo test set trong `src/evaluation/testset.py` hoặc bộ GX expectations trong `src/observability/quality.py`. Phần việc của tôi là kiểm tra các module đó, tích hợp chúng vào luồng Phase 1 và xác minh artifacts đầu ra.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Kiểm tra Checkpoint 2 | Evaluation set và ChromaDB | Xác nhận 10 câu hỏi đủ 4 loại và collection có 24 documents |
| Khôi phục môi trường chạy | Workspace Python | Sửa `.venv` bị mất interpreter và xác minh import dependencies |
| Kiểm tra bảo mật trước commit | Toàn repository | `.env`, `.venv`, Python/model cache không được stage |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Nối pipeline Phase 1 end-to-end | `src/pipelines/phase1.py` | Chạy ingestion → cleaning → GX/freshness → index → evaluation → report | `python script/run_phase1.py` exit code 0 |
| Sinh báo cáo baseline | `generate_phase1_report()` | Báo cáo Markdown có source, metrics, quality, freshness và artifact paths | `data/reports/phase1_report.md` |
| Sửa QA cho benchmark tiếng Việt | `_extract_answer()`, `answer_question()` | Nhận diện dấu ngoặc `‘…’` và 4 dạng câu hỏi tiếng Việt | `data/results/baseline_answers.json` |
| Làm embedding chạy lại khi offline | `_load_model()` | Ưu tiên Hugging Face local cache, chỉ tải online ở lần đầu | Chạy lại pipeline thành công khi network bị chặn |
| Làm indexing idempotent và portable | `LocalEmbeddingIndex.build/load()` | Tái sử dụng collection, xóa IDs cũ, persist path tương đối | Chroma count = 24 sau nhiều lần chạy |

Output chính của phần việc là `data/results/baseline_metrics.json`: 10 samples, `retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`, `judge_accuracy = 1.0`, `mean_judge_score = 5`. Các giá trị judge trong lần chạy này đến từ heuristic fallback vì custom LLM endpoint chưa được cấu hình; Ragas được bỏ qua theo cấu hình mặc định.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Scaffold ban đầu dừng tại `NotImplementedError`, nên chưa có entrypoint kết nối các module và chưa sinh được baseline metrics/report. Ngoài ra, QA chỉ hiểu keyword và dấu nháy tiếng Anh trong khi test set dùng tiếng Việt và dấu ngoặc cong. Sentence Transformers còn thực hiện metadata HEAD request dù model đã cache, khiến pipeline chạy lại thất bại trong môi trường offline.

### Cách triển khai

Pipeline đọc `crossref_records.json` khi không bật refresh, làm sạch dữ liệu với cùng `run_date`, lưu CSV/JSON, sau đó chạy quality gate trước khi index. Nếu GX thất bại, pipeline dừng để ngăn dữ liệu không đạt chuẩn vào serving layer. Khi quality pass, clean dataframe được embed và nạp vào collection `papers-baseline`; pipeline xác nhận số document trong collection phải bằng số dòng sạch. Test set 10 câu được tái sử dụng để đánh giá, metrics và answers được ghi ra JSON rồi tổng hợp thành báo cáo Markdown.

Ở tầng QA, tiêu đề trong dấu `‘…’`, `'…'` hoặc `"…"` được dùng để exact lookup trước khi kết hợp semantic retrieval. Loại câu hỏi tiếng Việt quyết định trường metadata trả về. Cách này làm cho benchmark đo đúng contract của bộ test thay vì phụ thuộc ngẫu nhiên vào việc embedding hiểu dấu câu.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | 24 `PaperRecord` từ `data/raw/crossref_records.json`, settings và test set 10 câu |
| Output | Clean CSV/JSON, Chroma collection, answers, metrics, GX/freshness artifacts và Phase 1 report |
| Module phụ thuộc | `ingestion.cleaning`, `observability.quality`, `evaluation.metrics`, `evaluation.testset`, `retrieval.index` |
| Module sử dụng output | RAG QA/evaluation và các bước corruption/repair tiếp theo |
| Điều kiện lỗi cần xử lý | Clean dataframe rỗng, GX fail, Chroma count sai, test set không đủ 10 câu, model chưa cache hoặc mất mạng |

### Cách xác minh

```bash
python script/run_phase1.py
python -c "import json, chromadb; from core.config import load_settings; s=load_settings(); m=json.loads(s.paths.baseline_metrics.read_text()); c=chromadb.PersistentClient(path=str(s.paths.chroma_dir)).get_collection(s.baseline_collection_name); print(c.count(), m['retrieval_hit_rate'], m['mean_token_f1'])"
```

- **Kết quả mong đợi:** Pipeline exit code 0; 24 clean rows; collection có 24 documents; metrics chứa Hit Rate và Token F1.
- **Kết quả thực tế:** `24 1.0 1.0`; GX success `true`; freshness `is_fresh = true`.
- **Artifact/log:** `data/results/baseline_metrics.json`, `data/quality/baseline_quality_report.json`, `data/reports/phase1_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Pipeline cần chạy lặp lại ổn định, kể cả khi model đã cache và mạng không khả dụng.
- **Các phương án đã cân nhắc:** Luôn khởi tạo model theo tên Hugging Face và chấp nhận network check; hoặc ưu tiên `local_files_only=True` rồi mới fallback sang tải online.
- **Phương án đã chọn:** Local-cache-first, online-fallback.
- **Lý do:** Giữ đúng model `all-MiniLM-L6-v2`, giảm phụ thuộc mạng và vẫn hỗ trợ setup lần đầu. Collection cũng được tái sử dụng và làm rỗng theo IDs thay vì delete/recreate, tránh sinh Chroma segments mồ côi sau mỗi lần chạy.
- **Bằng chứng quyết định phù hợp:** Pipeline chạy lại offline thành công, collection vẫn có đúng 24 documents và chỉ còn một active vector segment.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `WinError 10013 ... access a socket ... forbidden` khi Sentence Transformers gửi HEAD request tới Hugging Face; trước đó `.venv` cũng báo `No Python at ... cpython-3.12.12...`.
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_phase1.py` trong môi trường sandbox không có network.
- **Nguyên nhân gốc:** Interpreter do `uv` quản lý đã bị mất khỏi đường dẫn cũ; sau khi model được tải, Transformers vẫn kiểm tra metadata online thay vì dùng cache ngay.
- **Cách xử lý:** Khôi phục Python 3.12 cho venv; bổ sung local-cache-first trong `_load_model()`; giữ cache/interpreter ngoài Git qua `.gitignore`.
- **Cách xác minh sau khi sửa:** Chạy pipeline nhiều lần không cấp network và nhận `Complete: 24 papers, hit_rate=100.00%, mean_token_f1=1.0000`.
- **Điều học được:** “Đã cache model” chưa đồng nghĩa thư viện hoàn toàn offline; cần kiểm soát rõ chế độ load và kiểm thử lần chạy thứ hai.

## 7. Hiểu biết về luồng end-to-end

1. Crossref payload được parse thành raw records bất biến; cleaning chuẩn hóa text, ngày và danh sách, tính `age_days`, khử trùng lặp và ghép `text_for_embedding`. Clean rows sau khi qua quality gate mới được embed và nạp vào ChromaDB.
2. Mỗi câu hỏi lưu `ground_truth_doc_ids`. Retrieval hit khi một ID chuẩn xuất hiện trong các documents được lấy; câu trả lời được so với `ground_truth` bằng token F1 và judge/fallback judge.
3. Quality checks kiểm tra tính đầy đủ, duy nhất, độ dài, số dòng và validity. Freshness theo dõi tuổi dữ liệu theo SLA: stale ratio không được vượt 25% với ngưỡng 180 ngày.
4. Baseline, corrupted và repaired phải dùng cùng test set để thay đổi metrics phản ánh thay đổi dữ liệu/index, không phải thay đổi độ khó câu hỏi.
5. Repair chỉ được coi là thành công khi dữ liệu được tái tạo từ raw source đáng tin cậy, quality/freshness phục hồi và metrics repaired quay về gần baseline. Phần corruption/repair chưa nằm trong commit cá nhân này nên tôi chưa khẳng định kết quả của hai trạng thái đó.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.0000 | N/A | N/A | 10/10 câu lấy được ground-truth document |
| `mean_token_f1` | 1.0000 | N/A | N/A | QA trả đúng trường metadata/summary theo benchmark |
| `judge_accuracy` | 1.0000 | N/A | N/A | Heuristic fallback judge, chưa phải live LLM judge |
| `mean_judge_score` | 5.00 | N/A | N/A | Phù hợp với token F1 tuyệt đối |
| Quality checks | 6/6 pass | N/A | N/A | Không có expectation thất bại |
| Freshness status | Fresh | N/A | N/A | 0/24 stale rows; stale ratio 0% |

### Kết luận từ số liệu

Ở phạm vi baseline, clean data đạt 6/6 expectations và freshness SLA → 24 documents được index đầy đủ → 10/10 retrieval hits và mean token F1 bằng 1.0. Chưa có artifacts corrupted/repaired trong phần việc này, vì vậy chưa đủ bằng chứng để hoàn thành hai chuỗi nhân quả corruption → degradation và repair → recovery. Việc này cần được cập nhật sau khi `script/run_corruption_flow.py` chạy thành công trên cùng `data/eval/test_set.json`.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Orchestration cần có quality gate và invariant rõ ràng, chẳng hạn row count và Chroma count, thay vì chỉ gọi tuần tự các hàm.
2. Reproducibility gồm cả đường dẫn portable, hành vi offline của model và khả năng chạy lặp lại mà không sinh trạng thái thừa.
3. Benchmark RAG phải đồng bộ ngôn ngữ, dấu câu và contract trả lời; nếu không, metric thấp có thể do lỗi tích hợp chứ không phải retrieval kém.

### Nếu có thêm thời gian

Tôi sẽ bổ sung pytest end-to-end cho pipeline offline, kiểm tra collection count, schema metrics và report consistency; đồng thời cấu hình một LLM judge thật để so sánh với heuristic fallback và bật Ragas trong một lần đánh giá riêng.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** **Nguyễn Thành Vinh**  
**Ngày xác nhận:** 2026-09-26

Commit bằng chứng: `d519dc0 feat: complete baseline phase 1 pipeline`.
