# Báo Cáo Cá Nhân — Checkpoint 4: Synthetic Data Corruption & Đo Lường Suy Giảm

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Thành Nam |
| MSSV | 2A202602827 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | O4 |
| Vai trò chính | Synthetic Data Corruption Suite & đo lường suy giảm RAG |
| Repository | https://github.com/kascenite/K4-L3B-Day10-O4-Data-Pipeline-Data-Observability |
| Ngày hoàn thành | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Tiêm sáu kịch bản dữ liệu lỗi và ghi log | `src/ingestion/corruption.py`, `corrupt_clean_dataframe` | Clean dataframe và đường dẫn log | Dataframe corrupted; `data/results/corruption_log.json` | Hoàn thành |
| Chạy đánh giá RAG trên dữ liệu corrupted | `script/run_corruption_flow.py`; tích hợp qua `src/pipelines/corruption_flow.py` | Clean dataset, test set và baseline metrics | `data/results/corrupted_metrics.json`; corrupted answers và quality report | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Module được hỗ trợ | Kết quả |
|---|---|---|
| Chỉnh entrypoint để có thể chạy trực tiếp từ thư mục gốc repository | `script/run_corruption_flow.py`, `script/run_phase1.py` | Thêm `src/` vào import path khi chạy script |
| Xử lý trường metadata không phải lúc nào cũng có trong QA | `src/retrieval/qa.py` | Dùng giá trị thông báo dự phòng thay vì để flow dừng bằng `KeyError`; CP4–CP5 chạy được đến cuối |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Tạo các lỗi gồm mất bản ghi mới nhất, summary rỗng, noise, title bị cắt, ngày cũ và bản ghi trùng | `src/ingestion/corruption.py` | Log đủ sáu kịch bản; clean ban đầu có 24 dòng, bỏ 4 dòng mới nhất rồi thêm 2 bản sao, còn 22 dòng | `data/results/corruption_log.json`; `data/clean/papers_clean_corrupted.csv` |
| Đánh giá chất lượng RAG trên dữ liệu sau khi tiêm lỗi | `src/pipelines/corruption_flow.py`, `data/results/corrupted_metrics.json` | Với 10 câu hỏi, retrieval hit rate còn 0.5 và mean token F1 còn 0.7187 | Chạy `script/run_corruption_flow.py`; kiểm tra metrics JSON |
| Kiểm tra Quality Gate và Freshness | `data/quality/corrupted_quality_report.json` | Quality Gate fail ở 3/6 expectations; Freshness vẫn đạt SLA vì stale ratio 9.09%, thấp hơn ngưỡng 25% | Kiểm tra quality report và phần freshness trong cùng artifact |
| Chạy tiếp phần repair để kiểm tra toàn bộ flow | `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` | Sau repair, retrieval hit rate trở lại 1.0 và mean token F1 trở lại 1.0 | Đối chiếu báo cáo ba trạng thái |

Cụ thể, `corruption_log.json` ghi nhận 4 bản ghi mới nhất bị loại, 2 summary bị làm rỗng, 2 summary được chèn noise, 2 title bị cắt, 2 ngày xuất bản bị lùi và 2 bản ghi được nhân đôi. Trên bộ 10 câu hỏi đánh giá, retrieval hit rate giảm từ 1.0 xuống 0.5 khi chuyển sang trạng thái corrupted.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Phần này của pipeline cần tạo ra một số lỗi dữ liệu có thể gặp trong thực tế trước khi dữ liệu được đưa vào vector index. Đồng thời phải lưu lại thông tin về các lỗi đã tạo và đo xem chúng ảnh hưởng như thế nào đến retrieval và câu trả lời của RAG. Chỉ nhìn việc pipeline có chạy xong hay không thì chưa đủ, vì dữ liệu thay đổi vẫn có thể làm chất lượng giảm mà không gây lỗi rõ ràng.

### Cách triển khai

`corrupt_clean_dataframe` bắt đầu bằng việc copy clean dataframe, kiểm tra các cột bắt buộc và xác nhận trường ngày xuất bản có thể xử lý được. Sau đó hàm lần lượt áp dụng sáu loại corruption. Bốn bản ghi có ngày xuất bản mới nhất được loại ra, tương ứng 20% của 24 bản ghi. Với phần dữ liệu còn lại, từng kịch bản lấy mẫu 10% bằng random seed cố định để các lần chạy có thể lặp lại. Bước nhân đôi record được thực hiện sau các lỗi còn lại.

Sau khi corruption xong, hàm tính lại `summary_chars`, `age_days` và `text_for_embedding`. Nội dung dùng cho embedding vẫn gồm title, authors, published date, categories và summary. Log JSON lưu số lượng bản ghi bị tác động cùng các chỉ số dòng liên quan. Dataset corrupted sau đó được ghi ra file, chạy qua GX, tạo một Chroma index riêng và đánh giá bằng chính test set đã dùng cho baseline.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input | Clean dataframe có các cột `paper_id`, `title`, `summary`, `published`, `authors_joined`, `categories_joined`; đường dẫn output log |
| Output | Dataframe corrupted chứa sáu dạng lỗi, các trường text/age được tính lại; log JSON mô tả các lỗi đã tạo |
| Module phụ thuộc | `pandas`, `json`, `pathlib`; quality gate, Chroma index và evaluation pipeline |
| Module sử dụng output | `src/pipelines/corruption_flow.py` dùng các output để ghi artifacts, chạy observability và đánh giá RAG |
| Điều kiện lỗi cần xử lý | Nếu dataframe rỗng, thiếu cột bắt buộc hoặc `published` không parse được thì báo `ValueError`; với dataset nhỏ, bước drop latest vẫn phải giữ lại ít nhất một bản ghi |

### Cách xác minh

```powershell
$env:PYTHONUTF8 = '1'
.\\.venv\\Scripts\\python.exe script\\run_corruption_flow.py
```

- **Kết quả mong đợi:** Log có đủ sáu loại lỗi, GX phát hiện các vấn đề chất lượng, metrics của dữ liệu corrupted được ghi ra và flow chạy hết.
- **Kết quả thực tế:** Lệnh chạy đến `=== HOÀN TẤT ===`. Corrupted hit rate là `0.5000`, mean token F1 là `0.7187`; báo cáo cuối flow cho thấy baseline `1.0000` và repaired `1.0000` ở cả hai metric này.
- **Artifact/log:** `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/quality/corrupted_quality_report.json`, `data/reports/corruption_report.md`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Nếu không cố định cách lấy mẫu ngẫu nhiên thì các bản ghi bị ảnh hưởng có thể thay đổi sau mỗi lần chạy, khiến việc so sánh khó hơn.
- **Các phương án đã cân nhắc:** Lấy mẫu ngẫu nhiên không seed; luôn chọn các dòng đầu; hoặc lấy mẫu ngẫu nhiên với seed cố định.
- **Phương án đã chọn:** Dùng `random_state` cố định riêng cho từng loại corruption.
- **Lý do:** Cách này vẫn giữ được tính ngẫu nhiên tương đối trong việc chọn record nhưng kết quả và log có thể tái lập. Riêng phần drop latest chọn theo `published` để đúng với yêu cầu, không phụ thuộc thứ tự hiện tại của dataframe.
- **Bằng chứng quyết định phù hợp:** Log ghi rõ các dòng bị tác động và các lần chạy cho ra metrics corrupted nhất quán trên cùng bộ 10 câu hỏi.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi:** Khi chạy script trực tiếp xuất hiện `ModuleNotFoundError: No module named 'pipelines'`. Sau khi sửa import path, lần chạy tiếp theo gặp `KeyError: 'categories_joined'` trong QA.
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_corruption_flow.py` từ thư mục gốc repository.
- **Nguyên nhân gốc:** Entry point chưa đưa thư mục `src/` vào Python import path. Ngoài ra, một số metadata lấy từ Chroma có thể không có các trường tùy chọn nhưng QA lại truy cập như thể chúng luôn tồn tại.
- **Cách xử lý:** Thêm `src/` vào import path trong script runner; các trường metadata dùng để tạo câu trả lời được chuyển sang cách truy cập an toàn và có thông báo dự phòng nếu thiếu.
- **Cách xác minh sau khi sửa:** Chạy bằng Python trong `.venv` với `PYTHONUTF8=1`; toàn bộ flow chạy đến cuối và tạo được metrics/report.
- **Điều học được:** Khi debug pipeline cần kiểm tra cả cách gọi entrypoint từ thư mục gốc và dữ liệu metadata thực tế ở tầng retrieval. Trường tùy chọn không nên khiến toàn bộ bước đánh giá bị dừng.

## 7. Hiểu biết về luồng end-to-end

1. Dữ liệu từ Crossref được chuẩn hóa và làm sạch: bỏ markup, chuẩn hóa text, khử trùng lặp, tính tuổi dữ liệu và tạo `text_for_embedding`. Phần text này sau đó được embedding và lưu cùng metadata trong collection Chroma để phục vụ truy vấn.
2. Test set gồm câu hỏi, ground-truth answer và các document IDs mong đợi. Retrieval hit rate kiểm tra kết quả truy xuất có giao với các document IDs chuẩn hay không; token F1 và judge dùng để đánh giá mức độ đúng của câu trả lời so với ground truth.
3. Quality checks kiểm tra các thuộc tính của dữ liệu như số dòng, tính duy nhất và độ dài summary. Freshness monitoring tính tỷ lệ `age_days` lớn hơn 180 ngày và so với SLA tối đa 25%. Vì vậy, một dataset có thể làm GX fail nhưng Freshness vẫn pass.
4. Baseline, corrupted và repaired dùng cùng một test set nên việc đối chiếu có cùng điều kiện. Khi metrics thay đổi, nguyên nhân quan sát được đến từ dữ liệu hoặc index thay vì do đổi bộ câu hỏi.
5. Repair được xem là thành công khi dữ liệu được dựng lại từ raw records, Quality Gate và Freshness đều đạt, đồng thời metrics quay lại mức baseline. Trong lần chạy này, repaired dataset có 24 dòng, GX pass và hit rate/token F1 đều trở lại 1.0.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.0000 | 0.5000 | 1.0000 | Hit rate giảm một nửa ở dữ liệu corrupted và trở lại mức ban đầu sau repair |
| `mean_token_f1` | 1.0000 | 0.7187 | 1.0000 | Mức khớp giữa câu trả lời và ground truth giảm khi dữ liệu bị lỗi |
| `judge_accuracy` | 1.0000 | 0.7000 | 1.0000 | Judge đánh giá đúng 7/10 câu ở trạng thái corrupted |
| `mean_judge_score` | 5.0000 | 3.8000 | 5.0000 | Điểm trung bình giảm 1.2 điểm rồi quay lại mức baseline |
| Quality checks | PASS (24 dòng) | FAIL (3/6 checks; 22 dòng) | PASS (24 dòng) | Dataset corrupted fail ở row count, uniqueness và summary length |
| Freshness status | PASS (0/24 stale) | PASS (2/22 stale; 9.09%) | PASS (0/24 stale) | Có ngày bị lùi nhưng stale ratio vẫn dưới SLA 25% |

### Kết luận từ số liệu

1. Sau khi bỏ 4 bản ghi mới nhất, làm rỗng summary, chèn noise, cắt title, lùi ngày xuất bản và nhân đôi dòng, GX phát hiện các vấn đề về số dòng, duplicate `paper_id` và summary quá ngắn. Freshness vẫn pass với stale ratio 9.09%. Cùng lúc đó, retrieval hit rate giảm từ 1.0 xuống 0.5 và mean token F1 từ 1.0 xuống 0.7187.
2. Khi dựng lại dữ liệu từ raw records, Quality Gate pass trên 24 dòng và stale ratio trở về 0%. Hai metric retrieval hit rate và mean token F1 cũng phục hồi về 1.0.

Chưa thể nói riêng loại corruption nào gây ra phần lớn mức giảm vì cả sáu lỗi được áp dụng trong cùng một lượt và chưa có ablation cho từng lỗi. Tuy vậy, việc bỏ các bản ghi mới nhất có thể làm mất tài liệu cần thiết cho một số câu hỏi; summary bị rỗng hoặc có noise và title bị cắt cũng làm giảm lượng thông tin dùng cho retrieval và trả lời. Vì vậy, kết quả hiện tại nên được hiểu là tác động tổng hợp của cả sáu lỗi, không phải mức ảnh hưởng riêng của từng lỗi.

Một điểm khá rõ trong kết quả là Freshness vẫn pass dù có hai ngày xuất bản bị lùi. Stale ratio chỉ ở mức 9.09%, thấp hơn ngưỡng 25%. Điều này cho thấy SLA hiện tại chủ yếu kiểm tra tỷ lệ dữ liệu stale vượt ngưỡng, chứ không đảm bảo phát hiện mọi trường hợp ngày bị sửa sai. Ngoài ra, noise và title bị cắt chưa tạo ra failed expectation riêng trong bộ GX đang dùng.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Có log lineage cho từng kịch bản corruption giúp theo dõi chính xác lỗi nào đã được tạo và giúp việc chạy lại thí nghiệm dễ hơn.
2. Quality Gate và Freshness SLA không kiểm tra cùng một vấn đề, vì vậy cần xem cả hai khi đánh giá chất lượng dữ liệu.
3. Data lỗi vẫn có thể cho phép pipeline dựng index và chạy evaluation bình thường nhưng chất lượng RAG giảm đáng kể. Dùng cùng một benchmark giúp nhìn rõ mức giảm này bằng số liệu.

### Nếu có thêm thời gian

Có thể chạy ablation cho từng loại corruption riêng lẻ. Đồng thời bổ sung expectation cho title tối thiểu 8 ký tự, noise marker và freshness dựa trên thay đổi của ngày xuất bản. Sau đó chạy lại toàn bộ trên cùng test set để xem từng rule tác động và phát hiện lỗi tốt đến đâu.

## 10. Cam kết của thành viên

Trước khi nộp bài, tôi cần tự kiểm tra lại các mục sau:

- [ ] Nội dung báo cáo đúng với phần việc tôi đã làm và mức độ tôi thực sự hiểu.
- [ ] Tôi có thể trình bày được toàn bộ flow end-to-end, không chỉ module mình phụ trách.
- [ ] Mỗi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [ ] Tôi không ghi “đã chạy thành công” cho phần chưa có bằng chứng kiểm chứng.
- [ ] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không sao chép nguyên văn từ báo cáo nhóm hoặc báo cáo của thành viên khác.

**Họ và tên:** Nguyễn Thành Nam  
**Ngày xác nhận:** 2026-09-26
