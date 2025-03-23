import os
import json
import hashlib
from datetime import datetime


def get_file_hash(path, algo='md5'):
    hash_func = hashlib.md5() if algo == 'md5' else hashlib.sha1()
    try:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        return f"Ошибка при хешировании: {e}"


def get_repo_structure_with_content(path, read_extensions=(".py", ".json", ".md", ".txt")):
    def walk(current_path):
        structure = []
        for entry in os.scandir(current_path):
            if entry.name.startswith(".") or entry.name == "venv":
                continue
            if entry.is_dir():
                structure.append({
                    "name": entry.name,
                    "type": "directory",
                    "children": walk(entry.path)
                })
            elif entry.is_file():
                file_info = {
                    "name": entry.name,
                    "type": "file",
                    "size": os.path.getsize(entry.path),
                    "hash_md5": get_file_hash(entry.path, 'md5'),
                    "hash_sha1": get_file_hash(entry.path, 'sha1')
                }
                if entry.name.endswith(read_extensions):
                    try:
                        with open(entry.path, "r", encoding="utf-8") as f:
                            file_info["content"] = f.read()
                    except Exception as e:
                        file_info["content"] = f"⚠️ Ошибка при чтении файла: {e}"
                structure.append(file_info)
        return structure

    return {
        "name": os.path.basename(path),
        "type": "directory",
        "scanned_at": datetime.now().isoformat(),
        "children": walk(path)
    }


if __name__ == "__main__":
    repo_path = os.path.abspath(".")  # путь к текущему клонированному репозиторию
    result = get_repo_structure_with_content(repo_path)

    with open("repo_structure.json", "w", encoding="utf-8") as out:
        json.dump(result, out, ensure_ascii=False, indent=2)

    print("✅ JSON-файл со структурой проекта сохранён: repo_structure.json")
