"""Игровое поле «Сапёра»: расстановка мин и открытие клеток."""

from __future__ import annotations

import random
from collections import deque
from typing import Iterable, Iterator, List, Optional, Tuple

from src.models.cell import Cell, Mark

Position = Tuple[int, int]


class Board:
    """Прямоугольное поле из клеток rows × cols."""

    def __init__(self, rows: int, cols: int) -> None:
        """Создать пустое поле без мин."""
        if rows < 1 or cols < 1:
            raise ValueError("Размер поля должен быть положительным")
        self.rows = rows
        self.cols = cols
        self._grid = [[Cell(r, c) for c in range(cols)] for r in range(rows)]

    def __iter__(self) -> Iterator[Cell]:
        """Перебрать все клетки поля построчно."""
        for row in self._grid:
            yield from row

    def cell(self, row: int, col: int) -> Cell:
        """Вернуть клетку по координатам."""
        if not self.in_bounds(row, col):
            raise IndexError(f"Клетка ({row}, {col}) вне поля")
        return self._grid[row][col]

    def in_bounds(self, row: int, col: int) -> bool:
        """Проверить, что координаты лежат внутри поля."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def neighbors(self, row: int, col: int) -> Iterator[Cell]:
        """Перебрать до восьми соседей клетки (по сторонам и диагоналям)."""
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (dr or dc) and self.in_bounds(row + dr, col + dc):
                    yield self._grid[row + dr][col + dc]

    @property
    def mine_count(self) -> int:
        """Сколько мин на поле."""
        return sum(cell.is_mine for cell in self)

    @property
    def flag_count(self) -> int:
        """Сколько флажков поставил игрок."""
        return sum(cell.is_flagged for cell in self)

    @property
    def closed_safe_count(self) -> int:
        """Сколько безопасных клеток ещё не открыто."""
        return sum(not cell.is_mine and not cell.is_open for cell in self)

    def place_random_mines(self, count: int, safe: Optional[Position] = None,
                           rng: Optional[random.Random] = None) -> None:
        """Случайно расставить count мин.

        Клетка safe (первый ход игрока) и, если хватает места, все её
        соседи остаются без мин — так первый ход всегда открывает
        область, а не одну цифру.
        """
        total = self.rows * self.cols
        if not 0 < count < total:
            raise ValueError("Число мин должно быть от 1 до числа клеток - 1")

        forbidden = set()
        if safe is not None:
            forbidden = {safe} | {n.position for n in self.neighbors(*safe)}
            if total - len(forbidden) < count:
                # Мин слишком много — защищаем только саму клетку.
                forbidden = {safe}

        candidates = [cell.position for cell in self
                      if cell.position not in forbidden]
        rng = rng or random.Random()
        self.set_mines(rng.sample(candidates, count))

    def set_mines(self, positions: Iterable[Position]) -> None:
        """Расставить мины в заданные клетки и пересчитать цифры."""
        for cell in self:
            cell.is_mine = False
        for row, col in positions:
            self.cell(row, col).is_mine = True
        for cell in self:
            cell.adjacent = sum(n.is_mine
                                for n in self.neighbors(cell.row, cell.col))

    def open_area(self, row: int, col: int) -> List[Cell]:
        """Открыть клетку, а если рядом нет мин — и всю пустую область.

        Используется обход в ширину (BFS): от клетки с нулём волна
        расходится к соседям и останавливается на клетках с цифрами.
        Флажки не открываются. Возвращает открытые клетки в порядке
        обхода — по нему отрисовщик анимирует «волну».
        """
        start = self.cell(row, col)
        if start.is_open or start.is_flagged:
            return []

        self._open(start)
        opened = []
        queue = deque([start])
        while queue:
            cell = queue.popleft()
            opened.append(cell)
            if cell.is_mine or cell.adjacent > 0:
                continue
            for neighbor in self.neighbors(cell.row, cell.col):
                if not neighbor.is_open and not neighbor.is_flagged:
                    self._open(neighbor)
                    queue.append(neighbor)
        return opened

    @staticmethod
    def _open(cell: Cell) -> None:
        cell.is_open = True
        cell.mark = Mark.NONE  # открытая клетка теряет знак вопроса
