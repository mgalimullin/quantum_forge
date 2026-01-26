import json
import re
from pathlib import Path

# === SETTINGS ===
MARKDOWN_DIR = Path("knowledge_base")        # папка с .md файлами
REPLACEMENTS_FILE = Path("terms_map.json")
MAKE_BACKUP = False                     # True = сохранять .bak файлы


# =================
def load_replacements(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def match_case(replacement: str, original: str) -> str:
    """
    Приводит replacement к регистру original
    """
    if original.isupper():
        return replacement.upper()
    if original.islower():
        return replacement.lower()
    if original.istitle():
        return replacement.title()
    return replacement


def replace_case_insensitive(text: str, replacements: dict) -> str:
    # Сначала более длинные ключи (чтобы избежать конфликтов)
    for old in sorted(replacements, key=len, reverse=True):
        new = replacements[old]

        pattern = re.compile(re.escape(old), re.IGNORECASE)

        def repl(match):
            return match_case(new, match.group(0))

        text = pattern.sub(repl, text)

    return text


def process_markdown_files():
    replacements = load_replacements(REPLACEMENTS_FILE)

    for md_file in MARKDOWN_DIR.rglob("*.md"):
        original_text = md_file.read_text(encoding="utf-8")
        new_text = replace_case_insensitive(original_text, replacements)

        if new_text != original_text:
            if MAKE_BACKUP:
                backup_path = md_file.with_suffix(md_file.suffix + ".bak")
                backup_path.write_text(original_text, encoding="utf-8")

            md_file.write_text(new_text, encoding="utf-8")
            print(f"[UPDATED] {md_file}")
        else:
            print(f"[SKIPPED] {md_file}")


if __name__ == "__main__":
    process_markdown_files()
