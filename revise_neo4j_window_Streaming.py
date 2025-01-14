import json
import tkinter as tk
from tkinter import messagebox, filedialog
from py2neo import Graph, Node
from llama_cpp import Llama
import time

# 初始化模型
# model_path = "D:/lla/1216/zuixin/zuixin.gguf"
model_path = "D:\\lla\\new\\Llama3-8B-Chinese-Chat-q8_0-v1.gguf"
# model_path = "D:/lla/1202/test/test.gguf"
llm = Llama(model_path=model_path, n_gpu_layers=-1, verbose=False)

# 连接到 Neo4j 数据库
graph = Graph("neo4j://localhost:7687", auth=("neo4j", "yubaba0330+"))

class ChatSession:
    def __init__(self, llm, max_history=0):
        self.llm = llm
        self.messages = []
        self.max_history = max_history
        self.current_data_size = 0  # 用于记录当前消息列表的数据总量（字节数）

    def add_message(self, role, content):
        if isinstance(content, bytes):
            message_size = len(content)  # 直接计算 bytes 的长度
            content = content.decode('utf-8')  # 将 bytes 转为字符串
        else:
            message_size = len(content.encode('utf-8'))  # 对字符串进行 utf-8 编码并计算长度

        if self.current_data_size + message_size > self.max_history:
            while self.current_data_size + message_size > self.max_history and self.messages:
                removed_message = self.messages.pop(0)
                self.current_data_size -= len(removed_message['content'].encode('utf-8'))  # 删除消息时更新数据大小

        self.messages.append({"role": role, "content": content})
        self.current_data_size += message_size  # 更新当前数据大小

    def get_response_stream(self, user_input):
        self.add_message("user", user_input)  # 将用户输入加入消息历史
        messages_to_send = self.messages[-self.max_history:]  # 仅保留最新的消息

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
# 定义流式输出处理函数
def handle_stream_output(output):
    response = ""
    try:
        for chunk in output:
            delta = chunk['choices'][0]['delta']
            if 'role' in delta:
                print(f"{delta['role']}: ", end='', flush=True)
            elif 'content' in delta:
                content = delta['content']
                print(content, end='', flush=True)
                response += content

                text_output.insert(tk.END, content)  # 添加流的内容
                text_output.yview(tk.END)  # 滚动到最新内容
                text_output.update_idletasks()  # 强制更新界面
                # 使用 after() 方法异步插入内容，以避免界面阻塞
                # root.after(0, lambda: update_text(content))  # 将内容插入到text_output

    except Exception as e:
        print(f"处理流式响应时发生错误: {e}")
    return response

# 更新文本框内容的函数
def update_text(content):
    text_output.insert(tk.END, content)  # 添加流的内容
    text_output.yview(tk.END)  # 滚动到最新内容
    text_output.update_idletasks()  # 强制更新界面

def with_no_neo4j(question):
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


# 创建会话实例
chat_session = ChatSession(llm)

# 交互界面函数
def load_neo4j(question):
    text_output.insert(tk.END, "\n" + "*" * 60 + "\n\n")
    text_output.insert(tk.END, f"问题：{question}\n")
    text_output.insert(tk.END, "-" * 40 + "\n")
    results = {}
    # 查询，找到问题与给定文本相似的节点
    query = f"MATCH (n) WHERE apoc.text.levenshteinDistance(n.问题, '{question}') < 15 RETURN n ORDER BY n.问题 DESC"

    # 执行查询，获取结果
    result = graph.run(query).data()

    # 如果查询结果为空，直接将问题交给模型
    if not result:
        text_output.insert(tk.END, "知识图谱内未查询到该问题\n")
        text_output.insert(tk.END, "-" * 40 + "\n")
        text_output.insert(tk.END, "模型相应：\n")
        with_no_neo4j(question)

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
            if match_count > 5:
                match_scores.append((match_count, node))  # 将匹配字符数和节点一起加入列表

    # 排序匹配结果，匹配字符数最多的排在前面
    match_scores.sort(key=lambda x: x[0], reverse=True)  # 根据匹配字符数排序，字符数最多的最先

    # 获取最匹配的节点（字符匹配数最多的）
    if match_scores:
        text_output.insert(tk.END, "知识图谱内容：\n")
        best_match = match_scores[0][1]  # 获取字符匹配数最多的节点（即最匹配的节点）

        # 如果找到了最匹配的节点
        if best_match:
            # 将节点信息存入 results 字典
            for key, value in best_match.items():
                if key != '问题':  # 排除'问题'字段
                    results[key] = value
                    print(f"{key}: {value}")
                    text_output.insert(tk.END, f"{key}: {value}\n")
            text_output.insert(tk.END, "-" * 40 + "\n")
            text_output.update_idletasks()  # 强制更新界面
            print("-" * 40)  # 分隔符，方便查看不同项之间的内容

            # 截取结果的前500个字符，防止过长
            results_str = str(results)[:500]

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
        text_output.insert(tk.END, "知识图谱内未查询到该问题\n")
        text_output.insert(tk.END, "-" * 40 + "\n")
        text_output.insert(tk.END, "模型相应：\n")
        with_no_neo4j(question)

def create_data(data_path):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data["data"]:
        nodes_data = item["graph"]["nodes"]
        for node_data in nodes_data:
            labels = node_data["labels"]
            properties = node_data["properties"]
            node = Node(*labels, **properties)
            graph.create(node)
            text_output.insert(tk.END, f"Created node with labels {labels}: {properties}\n")
    text_output.insert(tk.END, "Data import completed!\n")

def mergr_data(data_path):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data["data"]:
        nodes_data = item["graph"]["nodes"]
        relationship_data = item["graph"]["relationships"]
        for node_data in nodes_data:
            labels = node_data["labels"]
            properties = node_data["properties"]
            query = f"""
            MERGE (n:{':'.join(labels)} {{ {', '.join([f"{k}: '{v}'" for k, v in properties.items()])} }})
            """
            graph.run(query)
            text_output.insert(tk.END, f"Processed node with labels {labels}: {properties}\n")

        if len(relationship_data) > 0:
            for relationship_datum in relationship_data:
                start_node = nodes_data[relationship_datum["startNode"]]
                end_node = nodes_data[relationship_datum["endNode"]]
                relationship_type = relationship_datum["type"]
                properties = relationship_datum["properties"]
                relationships = f"MERGE "

    text_output.insert(tk.END, "Data import completed!\n")

# GUI 界面
def query_data_from_listbox(event):
    selected_question = question_listbox.get(question_listbox.curselection())
    if selected_question:
        load_neo4j(selected_question)

def import_data():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        create_data(file_path)

def merge_data():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        mergr_data(file_path)

def query_from_entry():
    question = question_entry.get()
    if question:
        load_neo4j(question)

# 初始化 GUI
root = tk.Tk()
root.title("Neo4j 数据管理与模型查询")
root.geometry("900x600")  # 调整窗口大小

# 添加标题
title_label = tk.Label(root, text="知识图谱测试与查询系统", font=("Arial", 16, "bold"))
title_label.pack(pady=10)

# 添加使用说明
usage_label = tk.Label(root, text="1. 输入问题并点击查询，获取模型响应。"
                                  "\n2. 从问题列表中选择问题并查询。(双击查询、单击问题再点击查询按键)"
                                  "\n3. 可以导入或合并数据至Neo4j数据库。"
                                  "\n4. 推荐合并数据(避免重复数据)", font=("Arial", 12))
usage_label.pack(pady=10)

# 主容器，分为左右两部分
main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# 左侧容器：问题列表及按键
left_frame = tk.Frame(main_frame, width=450)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 添加问题列表
question_label = tk.Label(left_frame, text="知识图谱测试问题列表:\n(双击问题查询，等待1-3分钟模型响应)", font=("Arial", 12))
question_label.pack(pady=5)

question_listbox = tk.Listbox(left_frame, height=15)
questions = [
    "吊顶日常检查", "吊顶的维修和加固", "吊顶日常检查方法", "吊顶定期检查",
    "浮置矿棉板吊顶脱落原因及维修、加固方式", "铝条板吊顶脱落原因及维修、加固方式",
    "铝方板吊顶脱落原因及维修、加固方式", "勾搭铝板吊顶脱落原因及维修、加固方式",
    "纸面石膏板吊顶脱落原因及维修、加固方式", "固定式金属板吊顶脱落原因及维修、加固方式",
    "U型方通吊顶脱落原因及维修、加固方式", "垂片吊顶脱落原因及维修、加固方式",
    "格栅吊顶脱落原因及维修、加固方式", "挂钩板悬浮吊顶脱落原因及维修、加固方式",
    "吊顶检修口维修、加固方式"
]
for question in questions:
    question_listbox.insert(tk.END, question)
question_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
question_listbox.bind("<Double-1>", query_data_from_listbox)

# 输入框和查询按钮
entry_frame = tk.Frame(left_frame)
entry_frame.pack(pady=5)

question_entry = tk.Entry(entry_frame, font=("Arial", 12), width=30)
question_entry.pack(side=tk.LEFT, padx=5)

query_button = tk.Button(entry_frame, text="查询", font=("Arial", 12), command=query_from_entry)
query_button.pack(side=tk.LEFT, padx=5)

# 导入和合并数据按钮
data_frame = tk.Frame(left_frame)
data_frame.pack(pady=5)

import_button = tk.Button(data_frame, text="导入数据", font=("Arial", 12), command=import_data)
import_button.pack(side=tk.LEFT, padx=5)

merge_button = tk.Button(data_frame, text="合并数据", font=("Arial", 12), command=merge_data)
merge_button.pack(side=tk.LEFT, padx=5)

# 右侧容器：模型输出
right_frame = tk.Frame(main_frame, width=450)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

response_label = tk.Label(right_frame, text="\n模型响应：", font=("Arial", 12))
response_label.pack(pady=5)

text_output = tk.Text(right_frame, wrap="word", height=15)
text_output.pack(fill=tk.BOTH, expand=True, pady=5)

root.mainloop()