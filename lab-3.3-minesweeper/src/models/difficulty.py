"""Уровни сложности игры."""

from dataclasses import dataclass

MIN_SIDE = 5
MAX_ROWS = 24
MAX_COLS = 30


@dataclass(frozen=True)
class Difficulty:
    """Размер поля и число мин."""

    key: str      # идентификатор для таблицы рекордов
    title: str    # название для меню
    rows: int
    cols: int
    mines: int

    @property
    def label(self) -> str:
        """Подпись для меню, например «Новичок (9×9, 10 мин)»."""
        return f"{self.title} ({self.cols}×{self.rows}, {self.mines} мин)"


BEGINNER = Difficulty("beginner", "Новичок", 9, 9, 10)
INTERMEDIATE = Difficulty("intermediate", "Любитель", 16, 16, 40)
EXPERT = Difficulty("expert", "Профессионал", 16, 30, 99)
PRESETS = (BEGINNER, INTERMEDIATE, EXPERT)


def max_mines(rows: int, cols: int) -> int:
    """Наибольшее допустимое число мин для поля rows × cols.

    Как в классическом «Сапёре»: (rows - 1) * (cols - 1), чтобы на поле
    всегда оставалось место для безопасного первого хода.
    """
    return (rows - 1) * (cols - 1)


def custom(rows: int, cols: int, mines: int) -> Difficulty:
    """Создать особый уровень, приведя параметры к допустимым границам."""
    rows = max(MIN_SIDE, min(MAX_ROWS, int(rows)))
    cols = max(MIN_SIDE, min(MAX_COLS, int(cols)))
    mines = max(1, min(max_mines(rows, cols), int(mines)))
    return Difficulty("custom", "Особый", rows, cols, mines)
