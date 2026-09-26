# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Trần Nam Anh               |
| MSSV               | 2A202602901 |
| Khóa/Lớp         | K4-L3B                     |
| Tên nhóm         | O4                         |
| Vai trò chính    | Benchmark Evaluation & Vector Store Indexing (Checkpoint 2) |
| Repository         | https://github.com/kascenite/K4-L3B-Day10-O4-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-26                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------- |
| Benchmark Test Set Generation | `src/evaluation/testset.py`: `build_test_set` | `data/clean/papers_clean.json` (DataFrame 24 dòng sạch) | `data/eval/test_set.json` (10 câu hỏi chuẩn hóa qua 4 nhóm nghiệp vụ) | Hoàn thành |
| Embedding Pipeline | `src/retrieval/embeddings.py`: `_load_model`, `MiniLMEmbeddings` | Text content (`text_for_embedding`, query string) | Dense vector 384 chiều chuẩn hóa L2, manifest `data/embeddings/papers_embeddings.json` | Hoàn thành |
| Vector Store Indexing | `src/retrieval/index.py`: `LocalEmbeddingIndex.build`, `search`, `lookup` | Cleaned DataFrame & MiniLM embeddings | ChromaDB collection `papers-baseline` tại `data/chroma/chroma.sqlite3` | Hoàn thành |

Phần việc của tôi nhận đầu vào trực tiếp từ module Data Cleaning (`papers_clean.json` do thành viên phụ trách Ingestion bàn giao). Đầu ra của tôi là bộ dữ liệu benchmark (`test_set.json`) và Vector Store (`papers-baseline`) làm nền tảng trực tiếp cho Agentic RAG QA, pipeline đánh giá Phase 1 (`phase1.py`), cũng như các vòng đo lường độ suy giảm và phục hồi (`corruption_flow.py`).

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ------------------------------ | ------- |
| Tích hợp Ground-truth Document ID vào Metric Evaluator | Module `metrics.py` | Đảm bảo trường `ground_truth_doc_ids` sử dụng đúng chuẩn DOI làm khóa duy nhất để đo chính xác `retrieval_hit_rate` |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Sinh bộ 10 câu hỏi test benchmark | `src/evaluation/testset.py`: `build_test_set` | `data/eval/test_set.json` phủ đủ 4 nhóm: 3 summary, 3 authors, 2 date, 2 categories | Lệnh CP2 in: `Tín hiệu hoàn thành: Sinh được 10 câu hỏi test` |
| Triển khai MiniLM Embeddings | `src/retrieval/embeddings.py`: `MiniLMEmbeddings` | Embeddings model `sentence-transformers/all-MiniLM-L6-v2` với L2 normalization và CPU pinning | Chạy `embed_documents` và `embed_query` không phát sinh lỗi |
| Index toàn bộ 24 tài liệu sạch vào ChromaDB | `src/retrieval/index.py`: `LocalEmbeddingIndex` | Collection `papers-baseline` (24 vectors), HNSW Cosine distance | Lệnh nạp index in: `Đã load collection papers-baseline với 24 tài liệu` |

**Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:**
File `data/eval/test_set.json` gồm chính xác 10 câu hỏi benchmark được thiết kế mang tính đại diện . Mỗi câu hỏi đều có metadata truy vết chặt chẽ: `id` (q01-q10), `question_type` (summary, authors, date, categories), `question` định dạng tiếng Việt rõ ràng, `ground_truth` chi tiết và `ground_truth_doc_ids` chứa DOI chuẩn của bài báo trong corpus sạch. Đây là bộ thước đo bất biến (immutable benchmark) để đối chiếu công bằng giữa 3 trạng thái Baseline, Corrupted và Repaired.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong một hệ thống RAG, nếu không có bộ test chuẩn (ground truth) và một vector store được lập chỉ mục đúng quy cách, chúng ta sẽ không thể đo lường định lượng được năng lực tìm kiếm (retrieval quality) và mức độ suy giảm khi dữ liệu bị lỗi (Silent Failure). Phần việc của tôi xây dựng:
1. Bộ câu hỏi kiểm thử khách quan phủ khắp các khía cạnh thông tin của bài báo khoa học.
2. Hệ thống vector embedding và ChromaDB storage bảo đảm tính nhất quán giữa truy vấn và ngữ cảnh tài liệu.

### Cách triển khai

1. **Sinh bộ câu hỏi (`src/evaluation/testset.py`):**
   - Kiểm tra schema bắt buộc của DataFrame (`paper_id`, `title`, `summary`, `authors`, `published`).
   - Khử trùng lặp theo `paper_id` và xác thực số lượng tài liệu >= 10.
   - Chọn mẫu cố định (deterministic sampling) theo các index định sẵn nhằm đảm bảo tính tái lập (reproducibility):
     - 3 câu hỏi `summary`: trích xuất nội dung tóm tắt công trình.
     - 3 câu hỏi `authors`: chuẩn hóa danh sách tác giả từ chuỗi phân cách dấu phẩy.
     - 2 câu hỏi `date`: truy vấn ngày công bố theo chuẩn `YYYY-MM-DD`.
     - 2 câu hỏi `categories`: truy vấn danh mục bài báo, có cơ chế fallback xử lý khi Crossref không có trường `subject`.
   - Gắn `ground_truth_doc_ids` bằng DOI (`paper_id`) viết thường làm định danh duy nhất.

2. **Embedding & Vector Store (`src/retrieval/embeddings.py` & `src/retrieval/index.py`):**
   - Đóng gói mô hình `all-MiniLM-L6-v2` kế thừa từ `langchain_core.embeddings.Embeddings`.
   - Sử dụng `@lru_cache(maxsize=2)` và chỉ định `device="cpu"` nhằm tránh việc tải lại model nhiều lần và xung đột driver GPU.
   - Kích hoạt `normalize_embeddings=True` để đưa vector về độ dài đơn vị (unit length), giúp khoảng cách Cosine tương thích tối đa với inner product.
   - Tạo chunk tài liệu với định danh `record_id = f"{paper_id}::{index}"`, đính kèm metadata phong phú (`title`, `published`, `authors_joined`, `summary`, `pdf_url`).
   - Cấu hình ChromaDB collection với không gian HNSW cosine: `configuration={"hnsw": {"space": "cosine"}}`. Cơ chế `LocalEmbeddingIndex.build` tự động dọn dẹp ID cũ nếu collection đã tồn tại để đảm bảo tính Idempotent.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `data/clean/papers_clean.json` (DataFrame 24 records gồm 16 cột đã được làm sạch và validated bởi Great Expectations) |
| Output                         | `data/eval/test_set.json` (JSON list 10 items); `data/chroma/chroma.sqlite3` & `data/embeddings/papers_embeddings.json` (manifest index) |
| Module phụ thuộc             | `src/ingestion/cleaning.py`, `src/core/config.py`, `sentence-transformers`, `chromadb` |
| Module sử dụng output        | `src/retrieval/qa.py`, `src/evaluation/metrics.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Bảng dữ liệu sạch < 10 records, thiếu cột bắt buộc, abstract/title bị rỗng, trường `categories` không tồn tại trong metadata Crossref |

### Cách xác minh

Sử dụng môi trường conda `vin` và thiết lập `PYTHONPATH=src`:

```bash
# 1. Kích hoạt môi trường conda vin
conda activate vin

# 2. Xác minh sinh bộ test set CP2 (10 câu hỏi)
PYTHONPATH=src python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print(f'Tín hiệu hoàn thành: Sinh được {len(ts)} câu hỏi test')"

# 3. Xác minh nạp và đọc ChromaDB collection
PYTHONPATH=src python -c "from core.config import load_settings; from retrieval.index import LocalEmbeddingIndex; s=load_settings(); idx=LocalEmbeddingIndex.load(s); print(f'Tín hiệu hoàn thành: Đã load collection {idx.collection_name} với {len(idx.documents)} tài liệu')"
```

- **Kết quả mong đợi:**
  - Lệnh 2 in: `Tín hiệu hoàn thành: Sinh được 10 câu hỏi test`
  - Lệnh 3 in: `Tín hiệu hoàn thành: Đã load collection papers-baseline với 24 tài liệu`
- **Kết quả thực tế:** Cả hai lệnh chạy thành công 100%, in đúng tín hiệu nghiệm thu.
- **Artifact/log:** `data/eval/test_set.json`, `data/chroma/chroma.sqlite3`, `data/embeddings/papers_embeddings.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi sinh câu hỏi thuộc nhóm `categories` (câu hỏi q09 và q10), qua quan sát dữ liệu thực tế từ Crossref API, toàn bộ 24 bài báo tải về đều có trường `subject` rỗng, dẫn đến cột `categories_joined` trong dữ liệu sạch mang giá trị rỗng.
- **Các phương án đã cân nhắc:**
  1. *Phương án 1:* Bỏ hẳn nhóm câu hỏi `categories`, thay thế bằng 4 câu hỏi `summary` và 4 câu hỏi `authors` để tránh trường hợp đáp án rỗng.
  2. *Phương án 2:* Gán cứng câu hỏi hỏi về danh mục và thiết kế quy tắc fallback linh hoạt: nếu `categories` rỗng thì lấy `primary_category`, nếu vẫn rỗng thì đưa ra câu trả lời chuẩn xác nhận bản ghi không có thông tin: `"Bản ghi không có thông tin danh mục (categories)."`.
- **Phương án đã chọn:** Phương án 2.
- **Lý do:** Đáp ứng đúng yêu cầu của Checkpoint 2 (phải phủ đủ 4 nhóm nghiệp vụ: `summary`, `authors`, `date`, `categories`). Đồng thời, trong thực tế dữ liệu sản xuất, việc thông tin bị khuyết là điều thường xuyên xảy ra; việc thiết lập fallback rõ ràng giúp đánh giá năng lực của RAG Agent khi đối mặt với dữ liệu thiếu (hệ thống phải biết trả lời là không có thông tin thay vì bịa đặt - hallucination).
- **Bằng chứng quyết định phù hợp:** File `data/eval/test_set.json` sinh ra 2 câu hỏi q09, q10 với `ground_truth` tường minh. Khi chạy Phase 1 baseline, Agent trả lời chính xác và đạt `judge_accuracy = 1.0` trên toàn bộ 10 câu hỏi.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  Khi khởi tạo mô hình embedding nhiều lần trong các hàm con hoặc khi chuyển đổi giữa các module pipeline, xuất hiện cảnh báo tài nguyên và độ trễ tăng vọt do mô hình `all-MiniLM-L6-v2` bị nạp lại từ đầu vào bộ nhớ RAM.
- **Lệnh hoặc bước tái hiện:** Chạy kiểm thử hàm `search()` liên tục hoặc gọi `LocalEmbeddingIndex.build()` sau đó gọi tiếp QA Agent trong cùng một session.
- **Nguyên nhân gốc:** Class `MiniLMEmbeddings` ban đầu khởi tạo trực tiếp instance `SentenceTransformer(model_name)` mà không có cơ chế singleton hoặc caching, khiến mỗi lần instantiate class là một lần load lại trọng số mô hình từ ổ đĩa.
- **Cách xử lý:**
  Tách hàm tải mô hình `_load_model(model_name: str)` độc lập ra ngoài và áp dụng decorator `@lru_cache(maxsize=2)`, đồng thời cố định `device="cpu"`:
  ```python
  @lru_cache(maxsize=2)
  def _load_model(model_name: str) -> SentenceTransformer:
      return SentenceTransformer(model_name, device="cpu")
  ```
- **Cách xác minh sau khi sửa:** Chạy kiểm tra batch retrieval trên toàn bộ 10 câu hỏi test, thời gian nạp model chỉ xuất hiện ở câu hỏi đầu tiên, 9 câu tiếp theo chạy với độ trễ thấp (< 50ms/query), không phát sinh rò rỉ bộ nhớ.
- **Điều học được:** Với các tài nguyên nặng như Transformer embeddings model, luôn cần áp dụng cơ chế Caching / Singleton để đảm bảo hiệu năng và tính ổn định của pipeline.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**  
   Dữ liệu thô JSON được tải từ `api.crossref.org/works` và lưu snapshot nguyên bản tại `data/raw/`. Module cleaning lọc bỏ tag JATS/HTML, khử trùng lặp theo DOI, tính `age_days` và ghép các trường quan trọng thành `text_for_embedding`. Chuỗi text này được đưa qua mô hình `all-MiniLM-L6-v2` để sinh vector 384 chiều, sau đó nạp cùng metadata vào ChromaDB collection `papers-baseline` sử dụng khoảng cách Cosine.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**  
   Mỗi câu hỏi kiểm thử có `ground_truth_doc_ids` (chứa DOI của tài liệu gốc) và `ground_truth` (nội dung câu trả lời chuẩn). Khi kiểm thử:
   - `retrieval_hit_rate` kiểm tra xem trong top-k (k=4) tài liệu mà Vector Store trả về có chứa ít nhất một DOI nằm trong `ground_truth_doc_ids` hay không.
   - `mean_token_f1` so sánh độ trùng khớp từ ngữ (n-gram overlap) giữa câu trả lời sinh ra bởi LLM và `ground_truth`.
   - `judge_accuracy` / `mean_judge_score` sử dụng LLM Judge chấm điểm ngữ nghĩa câu trả lời so với ground truth trên thang điểm 1-5.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**  
   - Quality checks (qua Great Expectations) kiểm tra tính hợp lệ về mặt cấu trúc và nội dung tĩnh của từng dòng dữ liệu (Completeness, Uniqueness, Validity): bảng đủ 24 dòng, DOI không trùng, không chứa giá trị null, độ dài summary đạt chuẩn.
   - Freshness monitoring kiểm tra chiều thời gian (Timeliness): theo dõi tuổi của dữ liệu thông qua chỉ số `age_days`. Dữ liệu có thể hoàn hảo về mặt schema và quality checks nhưng vẫn bị "stale" (quá hạn SLA 180 ngày) nếu không được làm mới định kỳ.

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**  
   Để bảo đảm tính khách quan và khoa học của thực nghiệm (kiểm soát biến số). Khi tập câu hỏi kiểm thử được giữ cố định (benchmark không đổi), sự biến thiên của các chỉ số hiệu năng (Hit Rate, F1, Judge Score) hoàn toàn phản ánh sự thay đổi của chất lượng dữ liệu nền (từ sạch → bị tiêm lỗi → được phục hồi). Nếu đổi test set giữa các pha, kết quả so sánh sẽ mất hiệu lực.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**  
   Repair được coi là thành công khi thỏa mãn đồng thời:
   - Về Data Observability: Báo cáo chất lượng `repaired_quality_report.json` đạt `success = true` (0/6 expectation fail) và `repaired_freshness.json` báo cáo `is_fresh = true`.
   - Về Agent Quality: Các chỉ số trong `repaired_metrics.json` phục hồi trở lại mức tương đương hoặc bằng Baseline (`retrieval_hit_rate = 1.0`, `mean_token_f1 = 1.0`, `judge_accuracy = 1.0`, `mean_judge_score = 5.0`).
   - Về Artifact đối chiếu: `data/reports/corruption_report.md` thể hiện sự đảo chiều rõ ràng giữa 3 trạng thái.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |     1.00 |      0.50 |     1.00 | Bị giảm một nửa (50%) ở trạng thái lỗi do bài báo bị xóa hoặc summary bị làm nhiễu; phục hồi hoàn hảo về 100% sau repair |
| `mean_token_f1`      |     1.00 |    0.7187 |     1.00 | Suy giảm xuống ~0.72 khi dữ liệu bị lỗi; lấy lại mức 1.0 sau khi tái tạo index từ nguồn raw sạch |
| `judge_accuracy`     |     1.00 |      0.70 |     1.00 | Tỷ lệ câu trả lời đạt yêu cầu giảm 30% do thiếu ngữ cảnh hoặc nhận ngữ cảnh rác; phục hồi 100% |
| `mean_judge_score`   |     5.00 |      3.80 |     5.00 | Điểm đánh giá trung bình từ LLM Judge giảm mạnh từ 5.0 xuống 3.8; lấy lại điểm tuyệt đối 5.0 |
| Quality checks         | 6/6 pass |  3 failed | 6/6 pass | GX Validation cảnh báo FAIL ở corrupted (fail độ dài summary, row count, uniqueness); PASS toàn bộ sau repair |
| Freshness status       |    Fresh |     Fresh |    Fresh | Tỷ lệ stale của dữ liệu corrupted là 9.09% (vẫn nằm dưới ngưỡng cảnh báo 25% SLA nên vẫn tính là Fresh) |

### Kết luận từ số liệu

1. **Chuỗi nguyên nhân – bằng chứng 1 (Corruption):**  
   Tiêm lỗi dữ liệu (Drop 20% bản ghi mới nhất, xóa rỗng summary, chèn ký tự nhiễu) → Great Expectations Quality Gate phát hiện 3 Expectation vi phạm (`success = false`) → `retrieval_hit_rate` của RAG tụt từ **1.0000** xuống **0.5000**, `mean_token_f1` giảm từ **1.0000** xuống **0.7187** (hiện tượng Silent Failure khi Agent không tìm được đúng tài liệu cần trả lời).
2. **Chuỗi nguyên nhân – bằng chứng 2 (Repair):**  
   Thực thi luồng Idempotent Repair từ snapshot thô đáng tin cậy `data/raw/crossref_records.json` → Tái lập trình DataFrame sạch và kiểm dịch GX đạt 6/6 checks pass → Re-index lại ChromaDB giúp `retrieval_hit_rate` phục hồi từ **0.5000** về **1.0000** và `judge_accuracy` lấy lại mốc **1.0000**.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**  
Lỗi **Drop latest records (mất bản ghi)** và **Blank summary / Inject noise (xóa hoặc làm rác nội dung tóm tắt)** ảnh hưởng nặng nề nhất. Khi bản ghi bị drop, document ID hoàn toàn biến mất khỏi Vector Store khiến Hit Rate lập tức bằng 0 cho các câu hỏi tương ứng. Khi summary bị rác hoặc trống, embedding sinh ra bị trôi dạt ngữ nghĩa (semantic drift) khiến mô hình tìm kiếm trả về các chunk không liên quan, dẫn đến câu trả lời của RAG Agent bị sai lệch hoàn toàn.

**Kết quả nào khác với kỳ vọng ban đầu?**  
Ban đầu nhóm dự đoán việc lùi ngày xuất bản (Stale date corruption) sẽ khiến Freshness SLA báo động đỏ (`is_fresh = False`). Tuy nhiên trong thực tế kết quả chạy, chỉ có 2 bản ghi bị lùi ngày quá hạn (tỷ lệ 9.09%), chưa vượt qua ngưỡng trần cảnh báo SLA là 25%. Điều này chứng minh hệ thống cảnh báo hoạt động rất chính xác theo đúng ngưỡng (threshold) định lượng đã cấu hình chứ không báo động giả tùy tiện.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Kiến trúc pipeline cần bảo đảm tính Idempotent (chạy lại nhiều lần cho cùng kết quả) và phải luôn lưu trữ dữ liệu thô (raw immutable snapshot) trước khi áp dụng bất kỳ bước tiền xử lý nào để làm điểm tựa cho cơ chế tự phục hồi (self-healing).
2. **Về data quality/observability:** Data Observability không chỉ là unit test cho code mà là "chốt kiểm dịch" liên tục cho dữ liệu (Data Quality Gate). Nhờ có Great Expectations 1.x bắt lỗi ngay tại tầng trung gian, ta có thể chủ động ngăn chặn việc nạp dữ liệu rác vào Vector Store trước khi làm hỏng trải nghiệm người dùng.
3. **Về ảnh hưởng của data đến RAG agent:** RAG Agent cực kỳ nhạy cảm với chất lượng dữ liệu ("Garbage In, Garbage Out"). Một lỗi nhỏ trong metadata hoặc việc chèn nhiễu vào văn bản tóm tắt không làm ứng dụng crash (không văng exception) nhưng lại gây ra lỗi nghiêm trọng nhất: **Silent Failure** (trả lời sai nhưng trông có vẻ đúng).

### Nếu có thêm thời gian

Tôi sẽ nghiên cứu triển khai thêm cơ chế **Hybrid Search (kết hợp Dense Vector MiniLM + Sparse BM25 / Reciprocal Rank Fusion)** và mở rộng bộ câu hỏi đánh giá lên 50 câu hỏi tự động sinh đa tầng (multi-hop reasoning). Cách đo lường cải thiện: So sánh `retrieval_hit_rate` và latency khi truy vấn các từ khóa hiếm hoặc mã định danh đặc thù.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Nam Anh  
**Ngày xác nhận:** 2026-09-26
