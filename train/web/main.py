from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os

app = FastAPI() # 建立一個 Fast API application

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory="train/web/static"), name="static")

save_path = 'train/data/merge/train_v3_human.jsonl'

def load_jsonl(path='train/data/merge/train_v3.jsonl'):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return [json.loads(line) for line in f]

data = load_jsonl()

@app.get("/")
def read_root():
    return FileResponse('train/web/static/index.html')

@app.get("/content/{cid}")
def read_content(cid: int):
    if 0 <= cid < len(data):
        return data[cid]
    else:
        return {"error": "Content ID out of range", "max_id": len(data) - 1}

@app.post("/content/accept/{cid}")
def accept_content(cid: int):
    if 0 <= cid < len(data):
        # 確保目錄存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        # append line to a jsonl file
        with open(save_path, 'a', encoding='utf-8-sig') as f:
            f.write(json.dumps(data[cid], ensure_ascii=False) + '\n')
        return {"status": "accepted", "id": cid}
    else:
        return {"error": "Content ID out of range", "max_id": len(data) - 1}
        
@app.post("/content/reject/{cid}")
def reject_content(cid: int):
    if 0 <= cid < len(data):
        return {"status": "rejected", "id": cid}
    else:
        return {"error": "Content ID out of range", "max_id": len(data) - 1}

@app.get("/stats")
def get_stats():
    return {"total_count": len(data)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)