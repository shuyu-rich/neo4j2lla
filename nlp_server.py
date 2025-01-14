from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from transformers import LlamaForCausalLM, LlamaTokenizer
import os
import json
import torch
import asyncio

# FastAPI 实例
app = FastAPI()

# 模型路径
model_path = "D:/lla/1216"  # 本地 LLaMA 模型路径
tokenizer_path = "D:/lla/1216"  # 通常 tokenizer 和模型在同一目录下

# 加载 tokenizer 和模型
tokenizer = LlamaTokenizer.from_pretrained(tokenizer_path)  # 加载 tokenizer
model = LlamaForCausalLM.from_pretrained(model_path)  # 加载模型

# 将模型加载到正确的设备
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)


# 处理生成器流式输出
async def stream_answer(question: str):
    # 将输入文本编码成 token
    inputs = tokenizer(question, return_tensors="pt").to(device)

    # 流式生成，不设置最大生成长度
    num_tokens_generated = 0

    while True:
        output = model.generate(inputs["input_ids"], do_sample=True, top_k=50, temperature=0.7,
                                pad_token_id=tokenizer.eos_token_id)

        generated_text = tokenizer.decode(output[0], skip_special_tokens=True)

        # 输出当前生成的文本
        print(generated_text, end="", flush=True)

        # 每次返回当前生成的部分
        yield generated_text

        # 更新已生成的 token 数量
        num_tokens_generated = len(output[0])

        # 如果模型生成了结束符号，则停止生成
        if tokenizer.decode(output[0])[-len(tokenizer.eos_token):] == tokenizer.eos_token:
            break


# 根据请求类型分发任务
async def handle_request(data):
    request_type = data.get("request_type")

    if request_type == "qa":
        # 问答功能
        question = data.get("question")

        # 流式返回生成的答案
        answer_chunks = stream_answer(question)  # 这里是生成器，应该直接返回生成器对象

        # 将生成的每一块内容逐步返回给客户端
        return answer_chunks

    elif request_type == "image_retrieval":
        # 图像检索功能
        image_path = data.get("image_path")
        result = {"image_path": image_path, "description": "Sample image description"}
        return result

    elif request_type == "db_retrieval":
        # 数据库检索功能
        query = data.get("query")
        result = {"query": query, "result": "Sample database result"}
        return result

    else:
        return {"error": "Unknown request type"}


# WebSocket 路由
@app.websocket("/ws")
async def nlp_streaming(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            # 接收客户端的消息
            message = await ws.receive_text()
            data = json.loads(message)  # 假设是 JSON 格式

            # 根据请求类型处理任务并获取答案
            answer_chunks = await handle_request(data)

            # 流式返回生成器的每一块内容
            async for chunk in answer_chunks:
                await ws.send_text(json.dumps({"answer_chunk": chunk}))
                await asyncio.sleep(0.5)  # 模拟流式返回

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"发生错误: {e}")


# 启动 FastAPI 服务
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
