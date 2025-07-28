import time
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI

class ChatCompletionRequest(BaseModel):
    model: str = "mock-gpt-model"
    messages: list

app = FastAPI(title="OpenAI-compatible API")

from unsloth import FastVisionModel
from qwen_vl_utils import process_vision_info

model, tokenizer = FastVisionModel.from_pretrained(
    model_name = f"model_gemma3_27b_lora_v15_argument_change", # YOUR MODEL YOU USED FOR TRAINING
    load_in_4bit = True, # Set to False for 16bit LoRA
    max_seq_length = 128000
)
FastVisionModel.for_inference(model) # Enable for inference!

import base64
from io import BytesIO
from PIL import Image

def base64_to_pil_image(base64_str):
    if base64_str.startswith("data:image/png;base64,"):
        base64_str = base64_str.split(",", 1)[1]
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))
    return image

def process_format(data:list):
    data = data.copy()
    for row in data:
        # if row['role']=='system':
        #     row['role'] = 'user'

        if type(row['content']) is list:
            for i, content in enumerate(row['content']):                
                if content['type']=='image_url':
                    row['content'][i] = {'type':'image', 'image':base64_to_pil_image(content['image_url']['url'])}
        elif type(row['content']) is dict:
            # if row['content']['type']=='image_url':
            #         row['content'] = [{'type':'image', 'image':base64_to_pil_image(row['content']['image_url']['url'])}]
            # else:
            row['content'] = [row['content']]
    return data

@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    messages = process_format(request.messages)    
    input_text = tokenizer.apply_chat_template(messages, add_generation_prompt = True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = tokenizer(
        text = input_text,
        images = image_inputs,
        add_special_tokens = False,
        return_tensors = "pt",
    ).to("cuda")


    from transformers import TextStreamer
    text_streamer = TextStreamer(tokenizer, skip_prompt = True)
    response_tokens = model.generate(**inputs, streamer = text_streamer, max_new_tokens = 1280,
                    use_cache = True, temperature = 1.0, top_p = 0.95, top_k = 64)
    outs = tokenizer.batch_decode(response_tokens[:, inputs.input_ids.shape[1]:])[0]
    response_message = outs.replace(tokenizer.eos_token, "")

    return {
        "id": "1337",
        "object": "chat.completion",
        "created": time.time(),
        "model": request.model,
        "choices": [{
            "message": {
                "content": response_message,            
            },
        }],
        "usage":{
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    }

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)