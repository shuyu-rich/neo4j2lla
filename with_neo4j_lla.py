# 示例代码：查询图数据库的简单示例
import json
from py2neo import Graph, Node

# from transformers import LLaMATokenizer, LLaMAForCausalLM
#
# # 加载Tokenizer和模型
# tokenizer = LLaMATokenizer.from_pretrained("meta-llama/LLaMA-7b")
# model = LLaMAForCausalLM.from_pretrained("meta-llama/LLaMA-7b")
# 连接到 Neo4j 数据库
graph = Graph("http://localhost:7474", auth=("neo4j", "yubaba0330+"))
# 查询，找到key为"小李"的内容
# query = f"MATCH (n) WHERE n.名字 = '爱新觉罗·溥仪' RETURN n"


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


if __name__ == '__main__':
    chonce = input("请输入你的选择："
                   "\n0.查询数据\n1. 导入数据(有可能出现重复数据) \n2. 合并数据(避免重复数据，如果内容不同会缺少当前数据)\nq. 退出程序")

    if chonce == "2":

        data_path = input("请输入数据文件路径：")
        mergr_data(data_path)

    elif chonce == "q":
        # exit("程序已关闭")
        print("所有信息：")
        query = "MATCH (n) RETURN n"
        result = graph.run(query).data()
        for item in result:
            # 获取节点 'n'
            node = item.get('n', {})
            # 遍历节点中的每一项并打印
            for key, value in node.items():
                if key != '问题':
                    print(f"{key}: {value}")
            print("-" * 40)  # 分隔符，方便查看不同项之间的内容

