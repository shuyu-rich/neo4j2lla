import json

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
        # 初始化结果列表
        result = []

        # 遍历 JSON 数据中的每个 graph
        for item in data["data"]:
            graph = item.get("graph", {})
            nodes = graph.get("nodes", [])

            # 遍历每个节点
            for node in nodes:
                question = node["properties"].get("问题", "")
                for key, value in node["properties"].items():
                    # 跳过 "问题" 字段，因为它是 input
                    if key == "问题":
                        continue

                    # 构造目标结构
                    output_item = {
                        "instruction": f"根据此相关信息: {{{key}: {repr(value)[:(480-22-len(question)-len(key))]}}}，详细的回答此问题: {question}",
                        "input": question,
                        "output": value
                    }
                    result.append(output_item)

        # 保存到新的 JSON 文件
        with open("output2.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        print("转换完成！结果已保存到 output.json 文件中。")

if __name__ == "__main__":
    mergr_data("./data.json")