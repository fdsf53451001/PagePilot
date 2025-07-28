import random

input_path = r'train\data\merge\train_v3.jsonl'   # 請替換為你的檔案路徑
output_path_1 = r'd:\WebAssistant\train\data\merge\train_v3_train.jsonl'
output_path_2 = r'd:\WebAssistant\train\data\merge\train_v3_val.jsonl'
split_ratio = 0.9

with open(input_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

random.shuffle(lines)
split_index = int(len(lines) * split_ratio)

with open(output_path_1, 'w', encoding='utf-8') as f1:
    f1.writelines(lines[:split_index])

with open(output_path_2, 'w', encoding='utf-8') as f2:
    f2.writelines(lines[split_index:])

print(f'共 {len(lines)} 筆，split_1: {split_index} 筆，split_2: {len(lines) - split_index} 筆')