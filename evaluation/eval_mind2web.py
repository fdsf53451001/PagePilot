import json
import sys

def split_mind2web_based_on_evaluation(eval_file, base_dir):
    with open(eval_file, encoding='utf-8') as f:
        data = json.load(f)

    cases = 0
    success_step = 0
    
    # Lists to store task names by difficulty
    easy_tasks = []    # <= 5 steps
    medium_tasks = []  # 6-10 steps
    hard_tasks = []    # > 10 steps
    
    for row in data:
        # if row[1] == 1:
        cases += 1
        task_name = row[0].split('\\')[-1]
        task_steps = 0
        
        try:
            with open(f'{base_dir}/{task_name}/action_trajectory.json', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if line.strip() != '':
                        task_steps += 1
            success_step += task_steps
        except:
            task_steps = 15
            success_step += 15
        
        # Categorize tasks by step count
        if task_steps <= 5:
            easy_tasks.append(task_name)
        elif task_steps <= 10:
            medium_tasks.append(task_name)
        else:
            hard_tasks.append(task_name)
    
    # Save categorized tasks to a single JSON file
    categories = {
        'easy': easy_tasks,
        'medium': medium_tasks,
        'hard': hard_tasks
    }
    
    with open('evaluation/mind2web_split/mind2web_categories.json', 'w', encoding='utf-8') as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)
    
    if cases == 0:
        print("No successful cases found.")
        return
    
    print(f"Easy tasks (<=5 steps): {len(easy_tasks)}")
    print(f"Medium tasks (6-10 steps): {len(medium_tasks)}")
    print(f"Hard tasks (>10 steps): {len(hard_tasks)}")
    
def evaluate_success_rate_mind2web_category(eval_file='evaluation/auto_eval_result.json', categories_file='evaluation/mind2web_split/mind2web_categories.json'):
    # Load evaluation results
    with open(eval_file, encoding='utf-8') as f:
        data = json.load(f)
    
    # Load categories
    with open(categories_file, encoding='utf-8') as f:
        categories = json.load(f)
    
    # Create task name to success mapping
    task_results = {}
    for row in data:
        task_name = row[0].split('\\')[-1]
        task_results[task_name] = row[1]
    
    # Calculate success rates for each category
    for category_name, task_list in categories.items():
        total_tasks = len(task_list)
        successful_tasks = sum(1 for task in task_list if task_results.get(task, 0) == 1)
        
        if total_tasks > 0:
            success_rate = successful_tasks / total_tasks
            print(f"{category_name.capitalize()} tasks success rate: {success_rate:.4f} ({successful_tasks}/{total_tasks})")
        else:
            print(f"{category_name.capitalize()} tasks: No tasks found")
    
    # Overall success rate
    total_success = sum(1 for row in data if row[1] == 1)
    overall_rate = total_success / len(data)
    print(f"Overall success rate: {overall_rate:.4f} ({total_success}/{len(data)})")
    
if __name__ == "__main__":
    eval_file = 'evaluation/results/mind2web/auto_eval_result_mind2web_ft_llama32_v9.json'
    base_dir = 'results/dataset/mind2web_ft_llama32_v9'
    split_json_file = 'evaluation/mind2web_split/mind2web_categories.json'
    # split_mind2web_based_on_evaluation(eval_file, base_dir)
    evaluate_success_rate_mind2web_category(eval_file, split_json_file)