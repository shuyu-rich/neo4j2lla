# 示例代码：查询图数据库的简单示例
import json
from py2neo import Graph, Node
from llama_cpp import Llama

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 设置本地模型路径
model_path = "D:\\lla\\AutoPrompt-main\\GPT2Model"  # 替换为您的本地GPT-2模型路径

# 加载本地模型和 tokenizer
model = AutoModelForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# 确保 tokenizer 有填充标记
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token  # 使用 eos_token 作为填充标记

# 设置生成文本时的参数
max_length = 500  # 根据需要调整这个值
eos_token_id = tokenizer.eos_token_id  # 结束令牌的ID

def generate_text(prompt):
    # 编码输入并截断/填充到最大长度
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding="max_length", max_length=model.config.max_position_embeddings)
    input_ids = inputs.input_ids
    attention_mask = inputs.attention_mask  # 获取 attention_mask

    # 使用模型生成文本
    outputs = model.generate(
        input_ids,
        attention_mask=attention_mask,  # 传入 attention_mask
        max_new_tokens=max_length,  # 使用 max_new_tokens 控制生成的令牌数
        eos_token_id=eos_token_id,
        num_return_sequences=1,  # 只生成一个序列
        pad_token_id=tokenizer.pad_token_id,  # 如果需要的话，设置填充令牌的ID
        temperature=0.5,  # 设置温度为0.5，减少生成的随机性
        top_p=0.9,  # 设置 nucleus sampling 的概率阈值
        top_k=50  # 设置生成时的 top-k 采样，控制候选词的数量
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# 连接到 Neo4j 数据库
graph = Graph("http://localhost:7474", auth=("neo4j", "yubaba0330+"))

def load_neo4j(question):
    results = {}
    # 计数器
    num = 0
    # 查询，找到key为"小李"的内容
    query = f"MATCH (n) WHERE n.ask = '{question}' RETURN n"
    # 查询所有内容
    querys = "MATCH (n) RETURN n"
    result = graph.run(query).data()
    # results = graph.run(querys).data()
    # print("以下为所有数据")
    # for i in results:
    #     num += 1
    #     print(f"第{num}条数据：", i)
    # 遍历 result 列表
    for item in result:
        # 获取节点 'n'
        node = item.get('n', {})

        # 遍历节点中的每一项并打印
        for key, value in node.items():
            if key != 'ask':
                results[key] = value
                print(f"{key}: {value}")
        print("-" * 40)  # 分隔符，方便查看不同项之间的内容
    input_text = f"问题: {question}，根据此相关信息: {results}，最终生成答案:"
    # 将文本转换为utf-8编码的字节串
    # encoded_text = input_text.encode('utf-8')
    response = generate_text(input_text)
    if response:
        print("\n模型响应:", response)
    else:
        print("未能获取模型响应，请重试或检查连接。")


def create_data(data_path):
    """
    在当前脚本中，使用graph.create(node)，
    它会 创建新的节点。如果你再次运行相同的脚本，每次都会创建新的节点，
    即使这些节点的属性和标签是完全相同的，也不会检查重复的节点，因此会有重复的数据。
    举个例子，
    如果重复导入具有相同 name 和 born 属性的 Person 节点，
    Neo4j 会创建多个具有相同属性和标签的节点。数据会重复存储在数据库中。
    """
    # 读取 JSON 文件
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 遍历 JSON 数据并创建节点
    for item in data["data"]:
        # 获取每一条数据的 graph 部分
        nodes_data = item["graph"]["nodes"]  # graph -> nodes 是一个列表，包含多个节点

        for node_data in nodes_data:
            labels = node_data["labels"]  # 从节点数据中提取标签
            properties = node_data["properties"]  # 从节点数据中提取属性

            # 创建节点
            node = Node(*labels, **properties)  # 使用动态标签和属性

            # 将节点添加到 Neo4j 图数据库中
            graph.create(node)

            print(f"Created node with labels {labels}: {properties}")

    print("Data import completed!")

def mergr_data(data_path):
    """
    如果你希望避免导入重复的数据，可以使用 MERGE 语句，
    它会确保节点或关系的唯一性，如果节点已经存在，则不会创建新的节点，而是返回现有的节点。
    MERGE 语句的作用是：如果匹配的节点存在，什么都不做；如果不存在，则创建新的节点。
    """
    # 读取 JSON 文件
    print(data_path)
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        print(data)

    # 遍历 JSON 数据并创建或合并节点
    for item in data["data"]:
        # 获取每一条数据的 graph 部分
        nodes_data = item["graph"]["nodes"]  # graph -> nodes 是一个列表，包含多个节点

        for node_data in nodes_data:
            labels = node_data["labels"]  # 从节点数据中提取标签
            properties = node_data["properties"]  # 从节点数据中提取属性

            # 使用 MERGE 确保节点唯一性
            # 将 labels 和 properties 传递给 MERGE 语句，确保相同的属性组合不会重复创建节点
            query = f"""
            MERGE (n:{':'.join(labels)} {{ {', '.join([f"{k}: '{v}'" for k, v in properties.items()])} }})
            """
            graph.run(query)

            print(f"Processed node with labels {labels}: {properties}")

    print("Data import completed!")



import time
if __name__ == '__main__':
    while True:
        chonce = input("请输入你的选择："
                       "\n0.查询数据\n1. 导入数据(有可能出现重复数据) \n2. 合并数据(避免重复数据，如果内容不同会缺少当前数据)\nq. 退出程序")
        if chonce == "0":
            while True:
                question = input("”q“退出查询\n请输入查询问题：")
                if question == "q":
                    break
                else:
                    # 计时器
                    start_time = time.time()
                    load_neo4j(question)
                    # 结束计时
                    end_time = time.time()
                    print(f"耗时: {(end_time - start_time)} 秒")
        if chonce == "1":

            data_path = input("请输入数据文件路径：")
            create_data(data_path)

        elif chonce == "2":

            data_path = input("请输入数据文件路径：")
            mergr_data(data_path)

        elif chonce == "q":
            exit("程序已关闭")
