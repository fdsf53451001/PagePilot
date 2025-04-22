import pyarrow.parquet as pq
import pandas as pd
import json

parquet_file = pq.ParquetFile('data/Multimodal-Mind2Web/data/test_domain-00000-of-00011-26c55c12cbbcdc8e.parquet')
df = parquet_file.read().to_pandas()

# row = df.iloc[0]
# print(row['website'])
# print(row['screenshot'])

# list unique website
# websites = df['website'].unique()
# print(websites)

website_url_table = {
    'usps': 'https://www.usps.com/',
    'umich.edu' : 'https://umich.edu/',
    'allrecipes' : 'https://www.allrecipes.com/',
    'healthgrades' : 'https://www.healthgrades.com/',
    'cookpad' : 'https://cookpad.com/',
    'petfinder' : 'https://www.petfinder.com/',
    'theweathernetwork' : 'https://www.theweathernetwork.com/en',
    'accuweather' : 'https://www.accuweather.com/',
    'adoptapet' : 'https://www.adoptapet.com/', 
    'coinmarketcap' : 'https://coinmarketcap.com/',
    'finance.google' : 'https://www.google.com/finance/',
    'osu.edu' : 'https://www.osu.edu/',
    'webmd' : 'https://www.webmd.com/', 
    'reddit' : 'https://www.reddit.com/',
    'ups' : 'https://www.ups.com',
    'fedex' : 'https://www.fedex.com',
    'redfin' : 'https://www.redfin.com/',
    'stocktwits' : 'https://stocktwits.com/',
    'healthline' : 'https://www.healthline.com/',
    'apartments' : 'https://www.apartments.com/',
    'babycenter' : 'https://www.babycenter.com/'
}

# list unique annotation_id
annotation_ids = df['annotation_id'].unique()
# print(len(annotation_ids))

dataset = []

for i, annotation_id in enumerate(annotation_ids):
    # find df with annotation_id, and target_action_index=0
    df_annotation = df[(df['annotation_id'] == annotation_id) & (df['target_action_index'] == '0')].iloc[0]
    website_name = df_annotation['website']
    if website_name not in website_url_table:
        continue
    website_url = website_url_table[website_name]
    ques = df_annotation['confirmed_task']

    dataset.append({'task_id':annotation_id, 'id':f'mind2web-test0-{i}', 'web':website_url, 'ques':ques})

with open('data/Multimodal-Mind2Web/mind2web_test0.jsonl', 'w') as f:
    for item in dataset:
        f.write(json.dumps(item) + '\n')
    