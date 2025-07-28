import json

input_path = r'train\data\merge\train_v2.jsonl'   # 請替換為你的檔案路徑
output_path = r'train\data\merge\train_v3.jsonl'

format_error_pattern = "Format ERROR: Both 'Thought' and 'Action' should be included in your reply."
action_error_pattern = "The action you have chosen cannot be exected. Please double-check if you have selected the wrong Numerical Label or Action or Action format. Then provide the revised Thought and Action."

original_count = 0
filtered_count = 0

with open(input_path, 'r', encoding='utf-8') as fin, open(output_path, 'w', encoding='utf-8') as fout:
    for line in fin:
        original_count += 1
        if format_error_pattern in line or action_error_pattern in line:
            continue
        fout.write(line)
        filtered_count += 1

print(f'原始資料共 {original_count} 筆，已儲存 {filtered_count} 筆資料到 {output_path}')