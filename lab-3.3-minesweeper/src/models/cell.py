"""Клетка игрового поля."""

from dataclasses import dataclass
from enum import Enum


class Mark(Enum):
    """Пометка, которую игрок ставит на закрытую клетку."""

    NONE = "none"
    FLAG = "flag"          # игрок уверен, что здесь мина
    QUESTION = "question"  # игрок сомневается


@dataclass(eq=False)
class Cell:
    """Одна клетка поля.

    Сравнение по значению отключено (eq=False), поэтому клетки можно
    хранить в множествах и использовать как ключи словарей.
    """

    row: int
    col: int
    is_mine: bool = False
    adjacent: int = 0       # число мин среди восьми соседей
    is_open: bool = False
    mark: Mark = Mark.NONE

    @property
    def is_flagged(self) -> bool:
        """Стоит ли на клетке флажок."""
        return self.mark is Mark.FLAG

    @property
    def position(self) -> tuple:
        """Координаты клетки (строка, столбец)."""
        return self.row, self.col
