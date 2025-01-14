# 示例代码：查询图数据库的简单示例
import json
from py2neo import Graph, Node
from llama_cpp import Llama
import string

# 初始化模型
model_path = "D:\\lla\\Llama3-8B-Chinese-Chat-GGUF\\zuixin1216\\zuixin.gguf"
# model_path = "D:\\lla\\new\\Llama3-8B-Chinese-Chat-q8_0-v1.gguf"
llm = Llama(model_path=model_path, n_gpu_layers=-1, verbose=False)

# 连接到 Neo4j 数据库0
graph = Graph("neo4j://localhost:7687", auth=("neo4j", "yubaba0330+"))


def load_neo4j(question):
    question = question.translate(str.maketrans('', '', string.punctuation))
    results = {}
    # 查询，找到问题与给定文本相似的节点
    query = f"MATCH (n) WHERE apoc.text.levenshteinDistance(n.问题, '{question}') < 15 RETURN n ORDER BY n.问题 DESC"

    # 执行查询，获取结果
    result = graph.run(query).data()

    # 如果查询结果为空，直接将问题交给模型
    if not result:
        print("没有查询到相关节点，直接将问题交给模型。")

        # 将问题交给模型进行处理
        input_text = f"请根据以下问题进行回答: {question}"
        encoded_text = input_text.encode('utf-8')

        # 获取模型响应
        response = chat_session.get_response_stream(encoded_text)
        if response:
            print("\n模型响应:", response)
        else:
            print("未能获取模型响应，请重试或检查连接。")
        return

    best_match = None  # 用来存储最匹配的节点
    max_match_count = 0  # 用来记录当前最大匹配字符数
    match_scores = []  # 用于存储所有匹配的得分和节点

    # 遍历查询结果
    for item in result:
        # 获取节点 'n'
        node = item.get('n', {})
        question_text = node.get('问题', '')

        # 计算当前节点与输入问题的字符匹配数量
        if question_text:
            match_count = sum(1 for c in question if c in question_text)  # 计算匹配的字符数
            if match_count <= len(question_text):
                # 匹配上的字符数在问题的总字符上占比多少
                match_ratio = match_count / len(question_text)
                match_count = (match_ratio * match_count)
            # 筛选出匹配字符数一样的、匹配字符数大于问题的总字符的
            else:
                pass
            match_scores.append((match_count, node))  # 将匹配字符数和节点一起加入列表

    # 排序匹配结果，匹配字符数最多的排在前面
    match_scores.sort(key=lambda x: x[0], reverse=True)  # 根据匹配字符数排序，字符数最多的最先

    # 获取最匹配的节点（字符匹配数最多的）
    if match_scores:
        best_match = match_scores[0][1]  # 获取字符匹配数最多的节点（即最匹配的节点）

        # 如果找到了最匹配的节点
        if best_match:
            # 将节点信息存入 results 字典
            for key, value in best_match.items():
                if key != '问题':  # 排除'问题'字段
                    results[key] = value
                    print(f"{key}: {value}")

            print("-" * 40)  # 分隔符，方便查看不同项之间的内容

            # 截取结果的前500个字符，防止过长
            results_str = str(results)[:490]

            # 创建输入文本
            input_text = f"根据此相关信息: {results_str}，详细的回答此问题: {question}"

            # 将文本转换为utf-8编码的字节串
            encoded_text = input_text.encode('utf-8')

            # 获取模型响应
            response = chat_session.get_response_stream(encoded_text)
            if response:
                print("\n模型响应:", response)
            else:
                print("未能获取模型响应，请重试或检查连接。")
    else:
        print("没有找到匹配的节点。")


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


class ChatSession:
    def __init__(self, llm, max_history=0):
        self.llm = llm
        self.messages = []
        self.max_history = max_history
        self.current_data_size = 0  # 用于记录当前消息列表的数据总量（字节数）

    def add_message(self, role, content):
        # 判断 content 是否是 bytes 类型
        if isinstance(content, bytes):
            message_size = len(content)  # 直接计算 bytes 的长度
            content = content.decode('utf-8')  # 将 bytes 转为字符串
        else:
            message_size = len(content.encode('utf-8'))  # 对字符串进行 utf-8 编码并计算长度

        # 如果当前数据总量 + 新消息大小 超过最大限制，需要清理历史消息
        if self.current_data_size + message_size > self.max_history:
            while self.current_data_size + message_size > self.max_history and self.messages:
                removed_message = self.messages.pop(0)
                self.current_data_size -= len(removed_message['content'].encode('utf-8'))  # 删除消息时更新数据大小

        # 添加新消息
        self.messages.append({"role": role, "content": content})
        self.current_data_size += message_size  # 更新当前数据大小

    def get_response_stream(self, user_input):

        self.add_message("user", user_input)  # 将用户输入加入消息历史
        messages_to_send = self.messages[-self.max_history:]  # 仅保留最新的消息

        print(f"User: {messages_to_send}")
        try:
            output = self.llm.create_chat_completion(
                messages=messages_to_send,
                stream=True
            )
            response = handle_stream_output(output)  # 处理流式输出
            self.add_message("assistant", response.strip())  # 将模型回答加入消息历史
            return response.strip()
        except Exception as e:
            print(f"\n发生错误: {e}")
            return ""


# 定义流式输出处理函数
def handle_stream_output(output):
    response = ""
    try:
        # 对流式响应进行处理
        for chunk in output:
            delta = chunk['choices'][0]['delta']
            if 'role' in delta:
                print(f"{delta['role']}: ", end='', flush=True)
            elif 'content' in delta:
                content = delta['content']
                print(content, end='', flush=True)
                response += content
    except Exception as e:
        print(f"处理流式响应时发生错误: {e}")
    return response

# 创建会话实例
chat_session = ChatSession(llm)

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
