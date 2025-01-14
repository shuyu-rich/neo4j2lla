import llama_cpp

# 初始化 LLaMA 模型加载（假设是 gguf 格式）
model_path = "D:\\lla\\AutoPrompt-main\\GPT2Model"  # gguf 格式的模型文件路径

# 加载模型
llama = llama_cpp.Llama(model_path=model_path, n_gpu_layers=-1, verbose=False)


def extract_keywords(text):
    # 构造提示，告诉模型提取关键词
    prompt = f"请提取以下文本的关键字：{text}，并输出关键字的列表。"

    # 使用模型进行推理
    response = llama(prompt)

    return response


while True:
    inp = input("Input 'q' to exit\n")
    if inp == "q":
        break
    else:
        keywords = extract_keywords(inp)
        print(f"{keywords['choices']}")
        print(f"{keywords['choices'][0]['text']}")
