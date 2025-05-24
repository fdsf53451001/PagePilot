import json
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator 
from collections import Counter

def evaluate_success_rate(eval_file='evaluation/auto_eval_result.json'):
    with open(eval_file) as f:
        data = json.load(f)

    success = 0
    for row in data:
        if row[1] == 1:
            success += 1

    print(f"Success rate: {success/len(data)}")

def evaluate_success_rate_GAIA(eval_file='evaluation/auto_eval_result.json', level=1):
    with open(eval_file) as f:
        data = json.load(f)

    success = 0
    size = 0
    for row in data:
        if f'tasklevel{level}' in row[0]:
            if row[1] == 1:
                success += 1
            size += 1

    print(f"Success rate: {success/size}")

def evaluate_avg_step_success_case(eval_file, base_dir):
    with open(eval_file, encoding='utf-8') as f:
        data = json.load(f)

    success_case = 0
    success_step = 0
    for row in data:
        if row[1] == 1:
            success_case += 1
            task_name = row[0].split('\\')[-1]
            try:
                with open(f'{base_dir}/{task_name}/action_trajectory.json', encoding='utf-8') as f:
                    # action_data = json.load(f)
                    # success_step += len(action_data)
                    lines = f.readlines()
                    for line in lines:
                        if line!='':
                            success_step += 1
            except:
                success_step += 15
          

    print(f"Average step in success case: {success_step/success_case}")

def evaluate_success_rate_human(eval_file):
    with open(eval_file) as f:
        data = json.load(f)

    success = 0
    partial_success = 0
    for row in data:
        if row[2] == 1:
            success += 1
        elif row[2] == 2:
            partial_success += 1

    print(f"Success rate: {success/len(data)}")
    print(f"Partial success rate: {partial_success/len(data)}")

def evaluate_steps_success_rate(base_dir='results/dataset/chinese', eval_file='evaluation/auto_eval_result_chinese.json'):
    # retrieve sub directory
    action_success = {}
    for i in range(16):
        action_success[i] = [0, 0]

    with open(eval_file, encoding='utf-8') as f:
        auto_eval_data = json.load(f)

    for dir in [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]:
        with open(f'{base_dir}/{dir}/action_trajectory.json', encoding='utf-8') as f:
            data = json.load(f)
            action_step = len(data)

        for row in auto_eval_data:
            if dir in row[0]:
                if row[1] == 1:
                    action_success[action_step][0] += 1
                action_success[action_step][1] += 1
        
    print([action_success[i][0] for i in range(16)])

    # draw graph for success and non-success
    x = np.arange(16)
    y = [int(action_success[i][0]) for i in range(16)]
    z = [int(action_success[i][1]) for i in range(16)]
    z = [int(z[i]-y[i]) for i in range(16)]

    plt.ylim(0, max(y + z) * 1.1)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

    plt.bar(x, y, label='Success')
    plt.bar(x, z, bottom=y, label='Non-Success')

    plt.legend()
    plt.xlabel('Action Steps')
    plt.ylabel('Count')
    # plt.title('Success Rate by Action Steps')

    plt.show()


def evaluate_steps_success_rate_two_method(name1, base_dir1, eval_file1, name2, base_dir2, eval_file2):
    # retrieve sub directory
    action_success1 = {}
    action_success2 = {}
    for i in range(16):
        action_success1[i] = [0, 0]
        action_success2[i] = [0, 0]

    with open(eval_file1, encoding='utf-8') as f:
        auto_eval_data1 = json.load(f)

    with open(eval_file2, encoding='utf-8') as f:
        auto_eval_data2 = json.load(f)

    for dir in [d for d in os.listdir(base_dir1) if os.path.isdir(os.path.join(base_dir1, d))]:
        with open(f'{base_dir1}/{dir}/action_trajectory.json', encoding='utf-8') as f:
            data = json.load(f)
            action_step = len(data)

        for row in auto_eval_data1:
            if dir in row[0]:
                if row[1] == 1:
                    action_success1[action_step][0] += 1
                action_success1[action_step][1] += 1
    
    for dir in [d for d in os.listdir(base_dir2) if os.path.isdir(os.path.join(base_dir2, d))]:
        with open(f'{base_dir2}/{dir}/action_trajectory.json', encoding='utf-8') as f:
            data = json.load(f)
            action_step = len(data)

        for row in auto_eval_data2:
            if dir in row[0]:
                if row[1] == 1:
                    action_success2[action_step][0] += 1
                action_success2[action_step][1] += 1
    
    print([action_success1[i][0] for i in range(16)])
    print([action_success2[i][0] for i in range(16)])

    # draw graph for success and non-success
    x = np.arange(16)
    y1 = [int(action_success1[i][0]) for i in range(16)]
    z1 = [int(action_success1[i][1]) for i in range(16)]
    z1 = [int(z1[i]-y1[i]) for i in range(16)]

    y2 = [int(action_success2[i][0]) for i in range(16)]
    z2 = [int(action_success2[i][1]) for i in range(16)]
    z2 = [int(z2[i]-y2[i]) for i in range(16)]

    plt.ylim(0, max(y1 + z1 + y2 + z2) * 1.1)
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))

    colors = {
        'success_method1': '#4F81BD',  # 藍色
        'non_success_method1': '#A6CBE1',  # 淡藍色
        'success_method2': '#9BBB59',  # 綠色
        'non_success_method2': '#D8E4BC',  # 淡綠色
    }

    plt.bar(x-0.2, y1, width=0.4, label=f'Success ({name1})', color=colors['success_method1'])
    plt.bar(x-0.2, z1, bottom=y1, width=0.4, label=f'Non-Success ({name1})', color=colors['non_success_method1'])

    plt.bar(x+0.2, y2, width=0.4, label=f'Success ({name2})', color=colors['success_method2'])
    plt.bar(x+0.2, z2, bottom=y2, width=0.4, label=f'Non-Success ({name2})', color=colors['non_success_method2'])

    plt.legend()
    plt.xlabel('Action Steps')
    plt.ylabel('Count')
    # plt.title('Success Rate by Action Steps')

    plt.show()

def evaluate_steps_two_method(name1, base_dir1, eval_file1, name2, base_dir2, eval_file2):
    # retrieve sub directory
    action_success1 = {}
    action_success2 = {}
    for i in range(16):
        action_success1[i] = [0, 0]
        action_success2[i] = [0, 0]

    with open(eval_file1, encoding='utf-8') as f:
        auto_eval_data1 = json.load(f)

    with open(eval_file2, encoding='utf-8') as f:
        auto_eval_data2 = json.load(f)

    for dir in [d for d in os.listdir(base_dir1) if os.path.isdir(os.path.join(base_dir1, d))]:
        with open(f'{base_dir1}/{dir}/action_trajectory.json', encoding='utf-8') as f:
            data = json.load(f)
            action_step = len(data)

        for row in auto_eval_data1:
            if dir in row[0]:
                if row[1] == 1:
                    action_success1[action_step][0] += 1
                action_success1[action_step][1] += 1
    
    for dir in [d for d in os.listdir(base_dir2) if os.path.isdir(os.path.join(base_dir2, d))]:
        with open(f'{base_dir2}/{dir}/action_trajectory.json', encoding='utf-8') as f:
            data = json.load(f)
            action_step = len(data)

        for row in auto_eval_data2:
            if dir in row[0]:
                if row[1] == 1:
                    action_success2[action_step][0] += 1
                action_success2[action_step][1] += 1
    
    print([action_success1[i][0] for i in range(16)])
    print([action_success2[i][0] for i in range(16)])

    # draw graph for success and non-success
    x = np.arange(16)
    y1 = [int(action_success1[i][0]) for i in range(16)]
    y2 = [int(action_success2[i][0]) for i in range(16)]

    plt.plot(x, y1, label=f'{name1}')
    plt.plot(x, y2, label=f'{name2}')

    plt.legend()
    plt.xlabel('Action Steps')
    plt.ylabel('Number of Successes')
    # plt.title('Success Rate by Action Steps')

    plt.show()

def evaluate_action_category(eval_file1, eval_file2, dataset1_name, base_dir1, base_dir2, dataset2_name):
    def parse_action_data(base_dir, eval_file):
        action_distribution = Counter()
        with open(eval_file, encoding='utf-8') as f:
            data = json.load(f)

        for row in data:
            if row[1] == 1:  # Only consider successful cases
                task_name = row[0].split('\\')[-1]
                action_file = os.path.join(base_dir, task_name, 'action_trajectory.json')
                try:
                    with open(action_file, encoding='utf-8') as af:
                        print(action_file)
                        actions = json.load(af)
                        for action in actions:
                            action_key = action.get("action_key", "Unknown")
                            if action_key:  # Ensure action_key is not None
                                action_distribution[action_key] += 1
                except FileNotFoundError:
                    print(f"Action file not found: {action_file}")
        return action_distribution

    # Parse action data for both files
    action_dist1 = parse_action_data(base_dir1, eval_file1)
    action_dist2 = parse_action_data(base_dir2, eval_file2)

    # Combine keys for consistent plotting
    all_keys = set(action_dist1.keys()).union(set(action_dist2.keys()))
    all_keys = sorted(all_keys)

    # Prepare data for plotting
    counts1 = [action_dist1.get(key, 0) for key in all_keys]
    counts2 = [action_dist2.get(key, 0) for key in all_keys]

    # Plotting
    x = np.arange(len(all_keys))
    width = 0.35

    plt.bar(x - width/2, counts1, width, label= dataset1_name, color='#4F81BD')
    plt.bar(x + width/2, counts2, width, label= dataset2_name, color='#9BBB59')

    plt.xticks(x, all_keys, rotation=45, ha='right')
    plt.ylabel('Action Count')
    plt.xlabel('Action Category')
    plt.title('Action Distribution Comparison')
    plt.legend()
    plt.tight_layout()

    # plt.show()
    plt.savefig('evaluation/action_distribution_comparison.png', dpi=300, bbox_inches='tight')


if __name__ == '__main__':
    # eval_file = r'evaluation\results\auto_eval_result_GAIA2_gpt_4o.json'
    # base_dir = r'results\dataset\GAIA_gpt_4o\level2'

    # evaluate_success_rate(eval_file)
    # evaluate_avg_step_success_case(eval_file, base_dir)

    # evaluate_success_rate_GAIA(eval_file, level=2)
    # evaluate_steps_success_rate(base_dir,eval_file)
    # evaluate_success_rate_human(eval_file)

    # evaluate_steps_success_rate_two_method('PagePilot','results/dataset/arxiv','evaluation/auto_eval_result_arxiv.json','WebVoyager','results/dataset/arxiv_origin','evaluation/auto_eval_result_arxiv_origin.json')
    # evaluate_steps_two_method('PagePilot','results/dataset/arxiv','evaluation/auto_eval_result_arxiv.json','WebVoyager','results/dataset/arxiv_origin','evaluation/auto_eval_result_arxiv_origin.json')

    eval_file1 = r'evaluation\results\mind2web\auto_eval_result_mind2web_nodynamic_noassistant_nomarkdown.json'
    eval_file2 = r'evaluation\results\mind2web\auto_eval_result_mind2web.json'
    base_dir1 = r'results\dataset\mind2web_nodynamic_noassistant_nomarkdown'
    base_dir2 = r'results\dataset\mind2web'

    evaluate_action_category(eval_file1, eval_file2, 'WebVoyager', base_dir1, base_dir2, 'PagePilot')