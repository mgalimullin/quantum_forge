import time

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

start_time = time.time()

# 1. Загружаем документы
print('1. Загружаем документы')
loader = DirectoryLoader(
    "../Task2/knowledge_base",
    glob="**/*.md",
    loader_cls=TextLoader
)
documents = loader.load()
print(f'   Загружено документов: {len(documents)}')

# 2. Бьём на чанки
print('2. Бьём на чанки')
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
docs = text_splitter.split_documents(documents)
print(f'   Получено чанков: {len(docs)}')

# 3. Эмбеддинги
print('3. Эмбеддинги')
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# 4. FAISS индекс
print('4. FAISS индекс')
vectorstore = FAISS.from_documents(docs, embeddings)

# Сохранение индекса
print('5. Сохранение индекса')
vectorstore.save_local("faiss_index")

end_time = time.time()
elapsed_time = end_time - start_time

print('---')
print('ИТОГИ ПОСТРОЕНИЯ ИНДЕКСА')
print(f'Чанков в индексе: {len(docs)}')
print(f'Время генерации: {elapsed_time:.2f} секунд')
print('END')

