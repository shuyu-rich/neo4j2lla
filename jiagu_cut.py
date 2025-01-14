import jiagu


def seg_pos_ner(text):

    words = jiagu.seg(text) # 分词
    print("分词",words)

    pos = jiagu.pos(words) # 词性标注
    print("词性标注",pos)

    ner = jiagu.ner(words) # 命名实体识别
    print("命名实体识别",ner)

    words = jiagu.seg(text)
    print("中文分词",words)

    # jiagu.load_userdict('dict/user.dict') # 加载自定义字典，支持字典路径、字典列表形式。
    jiagu.load_userdict(['汉服和服装'])

    words = jiagu.seg(text)  # 自定义分词，字典分词模式有效
    print("自定义分词，字典分词模式有效",words)

    keywords = jiagu.keywords(text, 5)  # 关键词
    print("关键词:",keywords)

    knowledge = jiagu.knowledge(text)
    print(knowledge)

if __name__ == '__main__':
    """
    "吊顶日常检查", "吊顶的维修和加固", "吊顶日常检查方法", "吊顶定期检查",
    "浮置矿棉板吊顶脱落原因及维修、加固方式", "铝条板吊顶脱落原因及维修、加固方式",
    "铝方板吊顶脱落原因及维修、加固方式", "勾搭铝板吊顶脱落原因及维修、加固方式",
    "纸面石膏板吊顶脱落原因及维修、加固方式", "固定式金属板吊顶脱落原因及维修、加固方式",
    "U型方通吊顶脱落原因及维修、加固方式", "垂片吊顶脱落原因及维修、加固方式",
    "格栅吊顶脱落原因及维修、加固方式", "挂钩板悬浮吊顶脱落原因及维修、加固方式",
    "吊顶检修口维修、加固方式"
    """
    while True:
        text = input("（q退出程序）请输入一段中文文本：")
        if text == "q":
            exit("退出程序")
        seg_pos_ner(text)