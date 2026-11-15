import json
import os


class FileSaveRepository:
    """Handles saving and loading game state dict snapshots on disk."""
    def __init__(self, file_path: str = "savegame.json"):
        self.file_path = file_path

    def save(self, state_data: dict) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)

    def load(self) -> dict:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError("Файл збереження не знайдено.")
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
