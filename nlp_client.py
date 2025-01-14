import websockets
import asyncio
import json

async def send_message(request_type, data):
    try:
        # 连接到 WebSocket 服务端
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            # 构造请求数据
            request_data = {
                "request_type": request_type,
                **data  # 添加其他需要的字段
            }

            # 发送请求
            await websocket.send(json.dumps(request_data))

            # 接收并打印流式返回的数据
            try:
                while True:
                    response = await websocket.recv()
                    if response:
                        print(f"Received: {response}")
                    else:
                        print("没有接收到数据，服务端可能已关闭连接")
                        break
            except websockets.exceptions.ConnectionClosedError:
                print("连接已关闭，停止接收数据")

    except Exception as e:
        print(f"发生错误: {e}")

# 客户端主程序
if __name__ == "__main__":
    # 示例：问答请求
    question = "什么是日常检测?"
    context = ""  # 如果 context 不为空，确保服务器能处理这个数据
    # 客户端发送请求类型为 "qa"
    asyncio.run(send_message("qa", {"question": question, "context": context}))
