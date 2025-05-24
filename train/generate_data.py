import os
import json

def process_results(input_file, output_file):
    # Load the evaluation results
    with open(input_file, 'r', encoding='utf-8') as f:
        results = json.load(f)

    jsonl_data = []

    # Iterate through the results
    for item in results:
        folder_path, value = item
        if value == 1:
            interact_file = os.path.join(folder_path, 'interact_messages.json')
            if os.path.exists(interact_file):
                with open(interact_file, 'r', encoding='utf-8') as interact_f:
                    messages = json.load(interact_f)
                    jsonl_data.append({"messages": messages})

    print(f"Number of successful cases: {len(jsonl_data)}")

    # Write the output in JSONL format
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for entry in jsonl_data:
            out_f.write(json.dumps(entry) + '\n')

# Example usage
if __name__ == "__main__":
    input_file = r"evaluation\results\auto_eval_result_GAIA2_gemini_25_pro.json"
    output_file = r"train\train_GAIA2_gemini_25_pro.jsonl"
    process_results(input_file, output_file)
