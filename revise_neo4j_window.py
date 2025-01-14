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
graph = Graph("http://localhost:7474", auth=("neo4j", "yubaba0330+"))

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
            text_output.insert(tk.END, f"模型响应: {response}\n\n")
            self.add_message("assistant", response.strip())  # 将模型回答加入消息历史
            return response.strip()
        except Exception as e:
            print(f"\n发生错误: {e}")
            return ""

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
    except Exception as e:
        print(f"处理流式响应时发生错误: {e}")
    return response

# 创建会话实例
chat_session = ChatSession(llm)

# 交互界面函数
def load_neo4j(question):
    text_output.insert(tk.END, "*" * 70 + "\n")
    text_output.insert(tk.END, f"问题：{question}\n")
    text_output.insert(tk.END, "-" * 40 + "\n")
    text_output.insert(tk.END, "知识图谱内容：\n")
    results = {}
    num = 0
    query = f"MATCH (n) WHERE n.问题 = '{question}' RETURN n"
    result = graph.run(query).data()

    for item in result:
        node = item.get('n', {})

        for key, value in node.items():
            if key != '问题':
                results[key] = value
                text_output.insert(tk.END, f"{key}: {value}\n")
        text_output.insert(tk.END, "-" * 40 + "\n")
    results = str(results)[:500]
    input_text = f"根据此相关信息: {results}，详细的回答此问题: {question}"
    encoded_text = input_text.encode('utf-8')
    response = chat_session.get_response_stream(encoded_text)
    if response:
        pass
    else:
        text_output.insert(tk.END, "未能获取模型响应，请重试或检查连接。\n")

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
title_label.grid(row=0, column=0, columnspan=2, pady=10)

# 添加使用说明
usage_label = tk.Label(root, text="1. 输入问题并点击查询，获取模型响应。"
                                  "\n2. 从问题列表中选择问题并查询。(双击查询、单击问题再点击查询按键)"
                                  "\n3. 可以导入或合并数据至Neo4j数据库。"
                                  "\n4. 推荐合并数据(避免重复数据)", font=("Arial", 12))
usage_label.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

# 左侧：问题列表
question_label = tk.Label(root, text="知识图谱测试问题列表:\n(双击问题查询，双击完成需等待1-3分钟模型相应)")
question_label.grid(row=2, column=0, padx=10, pady=10)
# 右侧：模型相应
question_label = tk.Label(root, text="模型相应：")
question_label.grid(row=2, column=1, padx=10, pady=10)

# 添加问题列表
questions = [
    "吊顶日常检查", "吊顶的维修和加固", "吊顶日常检查方法", "吊顶定期检查",
    "浮置矿棉板吊顶脱落原因及维修、加固方式", "铝条板吊顶脱落原因及维修、加固方式",
    "铝方板吊顶脱落原因及维修、加固方式", "勾搭铝板吊顶脱落原因及维修、加固方式",
    "纸面石膏板吊顶脱落原因及维修、加固方式", "固定式金属板吊顶脱落原因及维修、加固方式",
    "U型方通吊顶脱落原因及维修、加固方式", "垂片吊顶脱落原因及维修、加固方式",
    "格栅吊顶脱落原因及维修、加固方式", "挂钩板悬浮吊顶脱落原因及维修、加固方式",
    "吊顶检修口维修、加固方式"
]

question_listbox = tk.Listbox(root, height=15, width=50)
for question in questions:
    question_listbox.insert(tk.END, question)

question_listbox.grid(row=3, column=0, padx=10, pady=10)
question_listbox.bind("<Double-1>", query_data_from_listbox)

# 右侧：输入框和输出区域
text_output = tk.Text(root, width=70, height=20)
text_output.grid(row=3, column=1, padx=10, pady=10)

# 下方：输入问题框和按钮
question_entry_label = tk.Label(root, text="输入问题：")
question_entry_label.grid(row=4, column=0, padx=10, pady=10)

question_entry = tk.Entry(root, width=50)
question_entry.grid(row=4, column=1, padx=10, pady=10)

# 按钮区域
button_frame = tk.Frame(root)
button_frame.grid(row=5, column=0, columnspan=2, pady=20)

query_button = tk.Button(button_frame, text="查询", command=query_from_entry)
query_button.pack(side="left", padx=10)

import_button = tk.Button(button_frame, text="导入数据", command=import_data)
import_button.pack(side="left", padx=10)

merge_button = tk.Button(button_frame, text="合并数据", command=merge_data)
merge_button.pack(side="left", padx=10)

# 启动 GUI
root.mainloop()