from __future__ import annotations

import pandas as pd
import json
import os

def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: str) -> pd.DataFrame:
    """Thực hiện tiêm nhiều dạng data corruption vào dataframe sạch và ghi log chi tiết[cite: 2]."""
    df_corrupted = df.copy()
    corruption_log = {}
    
    # Đảm bảo cột thời gian đúng định dạng
    df_corrupted['published'] = pd.to_datetime(df_corrupted['published'])
    
    # 1. Drop mot so latest records (Mất 20% bài mới nhất)[cite: 2]
    df_corrupted = df_corrupted.sort_values('published', ascending=False)
    drop_count = int(len(df_corrupted) * 0.2)
    dropped_indices = df_corrupted.index[:drop_count].tolist()
    
    df_corrupted = df_corrupted.iloc[drop_count:].copy()
    corruption_log['dropped_latest_records'] = {
        "count": drop_count,
        "affected_indices": [int(i) for i in dropped_indices]
    }
    
    # Định lượng số dòng bị lỗi cho các task tiếp theo (khoảng 10% data)
    sample_size = max(1, int(len(df_corrupted) * 0.1))
    
    # 2. Blank summary o mot so dong[cite: 2]
    idx_blank = df_corrupted.sample(sample_size).index
    df_corrupted.loc[idx_blank, 'summary'] = ""
    corruption_log['blank_summary'] = {
        "count": len(idx_blank),
        "affected_indices": [int(i) for i in idx_blank.tolist()]
    }
    
    # 3. Inject noise vao text (Vào cột summary của những dòng không bị blank)[cite: 2]
    idx_noise = df_corrupted.drop(idx_blank).sample(sample_size).index
    df_corrupted.loc[idx_noise, 'summary'] = df_corrupted.loc[idx_noise, 'summary'].astype(str) + " #@! NOISE_DATA !@#"
    corruption_log['injected_noise'] = {
        "count": len(idx_noise),
        "affected_indices": [int(i) for i in idx_noise.tolist()]
    }
    
    # 4. Lam title bi truncate (Cắt xuống dưới 8 ký tự)[cite: 2]
    idx_trunc = df_corrupted.sample(sample_size).index
    df_corrupted.loc[idx_trunc, 'title'] = df_corrupted.loc[idx_trunc, 'title'].astype(str).str[:7]
    corruption_log['truncated_title'] = {
        "count": len(idx_trunc),
        "affected_indices": [int(i) for i in idx_trunc.tolist()]
    }
    
    # 5. Lam published date cu di (Lùi ngày xuất bản về 365 ngày trước)[cite: 2]
    idx_stale = df_corrupted.sample(sample_size).index
    df_corrupted.loc[idx_stale, 'published'] = df_corrupted.loc[idx_stale, 'published'] - pd.Timedelta(days=365)
    corruption_log['stale_date'] = {
        "count": len(idx_stale),
        "affected_indices": [int(i) for i in idx_stale.tolist()]
    }
    
    # 6. Add duplicate rows (Nhân đôi dòng ngẫu nhiên)[cite: 2]
    duplicates = df_corrupted.sample(sample_size)
    original_dup_indices = duplicates.index.tolist()
    df_corrupted = pd.concat([df_corrupted, duplicates], ignore_index=True)
    corruption_log['duplicated_rows'] = {
        "count": len(duplicates),
        "original_indices_duplicated": [int(i) for i in original_dup_indices]
    }
    
    # 7. Rebuild `text_for_embedding`[cite: 2]
    df_corrupted['text_for_embedding'] = df_corrupted['title'].astype(str) + ". " + df_corrupted['summary'].astype(str)
    
    # Convert lại published thành string để xuất CSV/JSON an toàn
    df_corrupted['age_days'] = (pd.Timestamp.now() - df_corrupted['published']).dt.days
    df_corrupted['published'] = df_corrupted['published'].dt.strftime('%Y-%m-%d')
    
    # 8. Ghi corruption log vao output_log_path[cite: 2]
    os.makedirs(os.path.dirname(output_log_path), exist_ok=True)
    with open(output_log_path, 'w', encoding='utf-8') as f:
        json.dump(corruption_log, f, indent=4, ensure_ascii=False)
        
    print(f"[Corruption] Đã tiêm lỗi thành công. Log chi tiết lưu tại {output_log_path}")
    return df_corrupted