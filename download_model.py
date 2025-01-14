# Load model directly
from transformers import AutoModel
model = AutoModel.from_pretrained("allenai/longformer-base-4096")





# from sentence_transformers import SentenceTransformer
# from transformers import AutoModelForCausalLM, AutoTokenizer
# model_path = 'D:/Downloads/bge_large_zh_v1.5'
# # model = SentenceTransformer(model_path)
# model = AutoModelForCausalLM.from_pretrained(model_path)
# tokenizer = AutoTokenizer.from_pretrained(model_path)
#
# text = "This is a test document."
# embeddings = model.encode(text)
#
# # 计算嵌入向量与自身的相似度（通常为1，因为是自己与自己比较）
# similarities = model.similarity(embeddings, embeddings)
# print(similarities.shape)  # 应该输出一个形状为 (1, 1) 的数组
#
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# import os
# os.environ["OPENAI_API_KEY"] = "*****"
# openai_api_key = os.environ["OPENAI_API_KEY"]
# openai_llm_model = llm = ChatOpenAI(
#     model="gpt-4o-mini",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
# )
# from langchain.document_loaders import PyPDFLoader
# loader = PyPDFLoader(f"./CV_Emily_Davis.pdf")
# pages = loader.load_and_split()
#
# from itext2kg.documents_distiller import DocumentsDisiller, CV
# document_distiller = DocumentsDisiller(llm_model = openai_llm_model)
# IE_query = '''
# # DIRECTIVES :
# - Act like an experienced information extractor.
# - You have a chunk of a CV.
# - If you do not find the right information, keep its place empty.
# '''
# # 使用定义好的查询和输出数据结构提炼文档。
# distilled_cv = document_distiller.distill(documents=[page.page_content.replace("{", '[').replace("}", "]") for page in pages], IE_query=IE_query, output_data_structure=CV)
# # 将提炼后的文档格式化为语义部分。
# semantic_blocks_cv = [f"{key} - {value}".replace("{", "[").replace("}", "]") for key, value in distilled_cv.items() if value !=[] and value != ""  and value != None]
#
