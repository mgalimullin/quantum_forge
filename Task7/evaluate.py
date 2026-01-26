import json
import asker
from datetime import datetime
from typing import List

from asker import manual_rag_answer, load_vectorstore, load_embeddings
from yandex_llm import YandexGPT5Lite

GOLDEN_FILE = "golden_questions.txt"
LOG_FILE = "eval_logs.jsonl"
MIN_ANSWER_LENGTH = 50
REFUSAL_PHRASES = [
    "не знаю",
    "нет информации",
    "в базе знаний нет",
    "я не могу ответить"
]


def load_golden_questions(path: str) -> List[str]:
    """Load golden questions from txt file."""
    questions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            questions.append(line)
    return questions


def is_successful_answer(
    answer: str,
    sources: list
) -> bool:
    """Heuristic to determine if answer is successful."""

    if not sources:
        return False
    if len(answer) < MIN_ANSWER_LENGTH:
        return False
    if any(p in answer.lower() for p in REFUSAL_PHRASES):
        return False
    return True


def log_result(record: dict) -> None:
    """Append evaluation record to JSONL log."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    embeddings = load_embeddings()
    vectorstore = load_vectorstore(embeddings)

    questions = load_golden_questions(GOLDEN_FILE)

    print(f"Запуск тестирования ({len(questions)} вопросов)...\n")

    llm = YandexGPT5Lite(
        api_key=asker.YANDEX_API_KEY,
        folder_id=asker.YANDEX_FOLDER_ID,
        temperature=0.0,
    )
    for idx, question in enumerate(questions, start=1):
        print(f"[{idx}] {question}")

        result = manual_rag_answer(
            vectorstore=vectorstore,
            llm=llm,
            query=question
        )

        answer_text = str(result["result"])
        sources = result["source_documents"]

        success = is_successful_answer(
            answer=answer_text,
            sources=sources
        )

        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": question,
            "answer_length": len(answer_text),
            "chunks_found": len(sources),
            "success": success,
            "sources": [
                doc.metadata.get("source", "unknown")
                for doc in sources
            ],
        }

        log_result(record)

        print(
            "  → УСПЕХ" if success else "  → ПРОБЛЕМА",
            f"(чанков: {len(sources)})\n"
        )

    print("Тестирование завершено.")


if __name__ == "__main__":
    main()
