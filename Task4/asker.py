from typing import List, Optional

from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from langchain_classic.schema import Document

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from yandex_llm import YandexGPT5Lite


FAISS_INDEX_PATH = "/Users/m.galimullin/workspace/practicum/07_sprint/quantum_forge/Task3/faiss_index"
USE_RETRIEVAL_QA = False  # False -> manual RAG

YANDEX_API_KEY = "YANDEX_API_KEY"
YANDEX_FOLDER_ID = "YANDEX_FOLDER_ID"


# ---------------------------------------------------------------------
# Embeddings & VectorStore
# ---------------------------------------------------------------------

def load_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def load_vectorstore(
    embeddings: HuggingFaceEmbeddings,
) -> FAISS:
    return FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )


# ---------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------

def build_prompt() -> PromptTemplate:
    template = """
Ты — помощник, который отвечает
ИСКЛЮЧИТЕЛЬНО на основе предоставленных документов.

Всегда действуй по шагам:
1. Проанализируй контекст.
2. Выполни логическое рассуждение.
3. Дай финальный ответ.

Пример:
Q: Что такое HyperRelay?
A:
1. В документах указано, что HyperRelay — это протокол.
2. Он используется для передачи данных.
3. Следовательно, HyperRelay — это протокол передачи данных.

Контекст:
{context}

Вопрос:
{question}

Ответ (с объяснением шагов):
"""
    return PromptTemplate(
        input_variables=["context", "question"],
        template=template,
    )


# ---------------------------------------------------------------------
# RetrievalQA
# ---------------------------------------------------------------------

def create_retrieval_qa(
    vectorstore: FAISS,
) -> RetrievalQA:
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 4},
    )

    llm = YandexGPT5Lite(
        api_key=YANDEX_API_KEY,
        folder_id=YANDEX_FOLDER_ID,
        temperature=0.0,
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True,
        chain_type_kwargs={"prompt": build_prompt()},
    )


# ---------------------------------------------------------------------
# Manual RAG
# ---------------------------------------------------------------------

def retrieve_documents(
    vectorstore: FAISS,
    query: str,
    k: int = 4,
) -> List[Document]:
    return vectorstore.similarity_search(query, k=k)


def build_context(documents: List[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in documents)


def manual_rag_answer(
    vectorstore: FAISS,
    llm: YandexGPT5Lite,
    query: str,
) -> dict:
    documents = retrieve_documents(vectorstore, query)
    context = build_context(documents)

    if not documents:
        return {
            "result": "В базе знаний нет информации по этому вопросу.",
            "source_documents": [],
        }

    prompt = build_prompt()
    full_prompt = prompt.format(
        context=context,
        question=query,
    )

    answer = llm.invoke(full_prompt)

    return {
        "result": answer,
        "source_documents": documents,
    }


# ---------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------

def run_repl(
    vectorstore: FAISS,
    qa_chain: Optional[RetrievalQA],
) -> None:
    llm = YandexGPT5Lite(
        api_key=YANDEX_API_KEY,
        folder_id=YANDEX_FOLDER_ID,
        temperature=0.0,
    )

    print("RAG-бот запущен. Введите вопрос или 'exit'.\n")

    while True:
        query = input("Вопрос: ").strip()

        if query.lower() in ("exit", "quit"):
            print("Выход.")
            break

        if USE_RETRIEVAL_QA and qa_chain is not None:
            result = qa_chain(query)
        else:
            result = manual_rag_answer(
                vectorstore,
                llm,
                query,
            )

        print("\nОтвет:")
        print(result["result"])

        print("\nИсточники:")
        for doc in result["source_documents"]:
            source = doc.metadata.get("source", "unknown")
            print(f"- {source}")

        print("\n" + "-" * 60 + "\n")


def main() -> None:
    embeddings = load_embeddings()
    vectorstore = load_vectorstore(embeddings)

    qa_chain = None
    if USE_RETRIEVAL_QA:
        qa_chain = create_retrieval_qa(vectorstore)

    run_repl(vectorstore, qa_chain)


if __name__ == "__main__":
    main()
