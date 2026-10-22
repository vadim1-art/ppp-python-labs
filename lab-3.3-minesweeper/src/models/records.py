"""Таблица рекордов: лучшее время для каждого уровня сложности."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, Optional


class RecordsTable:
    """Лучшие результаты, сохраняемые в JSON-файл.

    Формат файла::

        {"beginner": {"time": 42, "date": "22.10.2026"}, ...}
    """

    def __init__(self, path: Path) -> None:
        """Загрузить таблицу из файла (если его нет — таблица пуста)."""
        self.path = Path(path)
        self._records: Dict[str, dict] = self._load()

    def best(self, key: str) -> Optional[dict]:
        """Лучший результат уровня key или None."""
        return self._records.get(key)

    def submit(self, key: str, seconds: int) -> bool:
        """Учесть результат. Возвращает True, если это новый рекорд."""
        current = self.best(key)
        if current is not None and current["time"] <= seconds:
            return False
        self._records[key] = {"time": int(seconds),
                              "date": date.today().strftime("%d.%m.%Y")}
        self._save()
        return True

    def clear(self) -> None:
        """Удалить все рекорды."""
        self._records = {}
        self._save()

    def _load(self) -> Dict[str, dict]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}  # файла нет или он повреждён — начинаем с нуля
        if not isinstance(data, dict):
            return {}
        return {key: value for key, value in data.items()
                if isinstance(value, dict)
                and isinstance(value.get("time"), int)}

    def _save(self) -> None:
        try:
            self.path.write_text(
                json.dumps(self._records, ensure_ascii=False, indent=2),
                encoding="utf-8")
        except OSError:
            pass  # не удалось сохранить — игра продолжается без рекордов
