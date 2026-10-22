"""Отрисовка игрового поля на холсте tkinter."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from src.config import (BEVEL, CELL_SIZE, COLOR_CROSS, COLOR_EXPLODED,
                        COLOR_FACE, COLOR_FLAG, COLOR_GRID, COLOR_LIGHT,
                        COLOR_MINE, COLOR_OPEN, COLOR_SHADOW,
                        EXPLOSION_STEP_MS, MAX_EXPLOSION_TIME_MS,
                        MAX_REVEAL_TIME_MS, NUMBER_COLORS, NUMBER_FONT,
                        REVEAL_STEP_MS)
from src.models.cell import Cell, Mark
from src.models.game import MinesweeperGame


class BoardRenderer:
    """Рисует клетки поля и анимирует их открытие.

    Отрисовщик только читает состояние игры и ничего в нём не меняет.
    Каждая клетка рисуется набором примитивов с общим тегом, поэтому
    её можно перерисовать отдельно, не трогая остальное поле.
    """

    def __init__(self, canvas: tk.Canvas, game: MinesweeperGame,
                 cell_size: int = CELL_SIZE) -> None:
        """Привязать отрисовщик к холсту и игре."""
        self.canvas = canvas
        self.game = game
        self.size = cell_size
        # Номер «поколения» отрисовки. Отложенные кадры анимации
        # проверяют его и не рисуют ничего, если поле уже сменилось.
        self._generation = 0

    @property
    def pixel_size(self) -> Tuple[int, int]:
        """Размер поля в пикселях (ширина, высота)."""
        board = self.game.board
        return board.cols * self.size, board.rows * self.size

    def cell_at(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """Клетка (строка, столбец) под точкой холста или None."""
        row, col = int(y // self.size), int(x // self.size)
        if x < 0 or y < 0 or not self.game.board.in_bounds(row, col):
            return None
        return row, col

    # ---------------------------------------------------------------
    # Отрисовка
    # ---------------------------------------------------------------

    def draw_board(self) -> None:
        """Полностью перерисовать поле (новая игра, смена уровня)."""
        self._generation += 1
        self.canvas.delete("all")
        width, height = self.pixel_size
        self.canvas.configure(width=width, height=height)
        for cell in self.game.board:
            self.draw_cell(cell)

    def draw_cell(self, cell: Cell, pressed: bool = False,
                  reveal: bool = False) -> None:
        """Нарисовать одну клетку.

        pressed — клетка «вдавлена» под зажатой кнопкой мыши;
        reveal — показать содержимое после проигрыша (мину или
        зачёркнутый неверный флажок).
        """
        tag = f"cell_{cell.row}_{cell.col}"
        self.canvas.delete(tag)
        x0, y0 = cell.col * self.size, cell.row * self.size
        box = (x0, y0, x0 + self.size, y0 + self.size)

        wrong_flag = reveal and cell.is_flagged and not cell.is_mine
        hidden_mine = reveal and cell.is_mine and not cell.is_flagged

        if cell.is_open or wrong_flag or hidden_mine:
            exploded = cell is self.game.exploded
            self._draw_open(box, tag, COLOR_EXPLODED if exploded
                            else COLOR_OPEN)
            if cell.is_mine or wrong_flag:
                self._draw_mine(box, tag)
                if wrong_flag:
                    self._draw_cross(box, tag)
            elif cell.adjacent:
                self._draw_number(box, tag, cell.adjacent)
        elif pressed:
            self._draw_open(box, tag, COLOR_OPEN)
        else:
            self._draw_raised(box, tag)
            if cell.mark is Mark.FLAG:
                self._draw_flag(box, tag)
            elif cell.mark is Mark.QUESTION:
                self._draw_question(box, tag)

    def draw_cells(self, cells: Iterable[Cell], **options: bool) -> None:
        """Перерисовать несколько клеток."""
        for cell in cells:
            self.draw_cell(cell, **options)

    # ---------------------------------------------------------------
    # Анимации
    # ---------------------------------------------------------------

    def animate_reveal(self, cells: Sequence[Cell],
                       origin: Tuple[int, int]) -> None:
        """Открыть клетки «волной», расходящейся от клетки origin.

        Задержка каждой клетки пропорциональна расстоянию Чебышёва
        (max(|dx|, |dy|)) до точки клика — получаются квадратные
        «кольца», как у волны от брошенного в воду камня.
        """
        rings = self._group_by_distance(cells, origin)
        if len(rings) <= 1:
            self.draw_cells(cells)
            return
        step = min(REVEAL_STEP_MS, MAX_REVEAL_TIME_MS // len(rings))
        self._schedule(rings, step, reveal=False)

    def animate_explosion(self) -> None:
        """После проигрыша по очереди показать все мины и ошибки."""
        exploded = self.game.exploded
        self.draw_board()
        if exploded is None:
            return
        targets = [cell for cell in self.game.board
                   if cell is not exploded and not cell.is_open
                   and (cell.is_mine != cell.is_flagged)]
        rings = self._group_by_distance(targets, exploded.position)
        if not rings:
            return
        step = min(EXPLOSION_STEP_MS, MAX_EXPLOSION_TIME_MS // len(rings))
        self._schedule(rings, step, reveal=True, delay=step)

    def _schedule(self, rings: List[List[Cell]], step: int, *,
                  reveal: bool, delay: int = 0) -> None:
        generation = self._generation
        for index, ring in enumerate(rings):
            self.canvas.after(delay + index * step,
                              self._draw_ring(generation, ring, reveal))

    def _draw_ring(self, generation: int, ring: List[Cell],
                   reveal: bool) -> Callable[[], None]:
        def draw() -> None:
            if generation == self._generation:
                self.draw_cells(ring, reveal=reveal)
        return draw

    @staticmethod
    def _group_by_distance(cells: Iterable[Cell],
                           origin: Tuple[int, int]) -> List[List[Cell]]:
        rings: dict = {}
        for cell in cells:
            distance = max(abs(cell.row - origin[0]),
                           abs(cell.col - origin[1]))
            rings.setdefault(distance, []).append(cell)
        return [rings[d] for d in sorted(rings)]

    # ---------------------------------------------------------------
    # Графические примитивы
    # ---------------------------------------------------------------

    def _draw_raised(self, box: Tuple[int, int, int, int], tag: str) -> None:
        """Закрытая клетка: светлая рамка сверху-слева, тень снизу-справа."""
        x0, y0, x1, y1 = box
        b = BEVEL
        c = self.canvas
        c.create_rectangle(x0, y0, x1, y1, fill=COLOR_FACE, width=0,
                           tags=tag)
        c.create_polygon(x0, y0, x1, y0, x1 - b, y0 + b, x0 + b, y0 + b,
                         x0 + b, y1 - b, x0, y1, fill=COLOR_LIGHT, tags=tag)
        c.create_polygon(x1, y1, x0, y1, x0 + b, y1 - b, x1 - b, y1 - b,
                         x1 - b, y0 + b, x1, y0, fill=COLOR_SHADOW, tags=tag)

    def _draw_open(self, box: Tuple[int, int, int, int], tag: str,
                   fill: str) -> None:
        """Открытая клетка: плоский фон и тонкая линия сетки."""
        x0, y0, x1, y1 = box
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, width=0,
                                     tags=tag)
        self.canvas.create_line(x0, y1 - 1, x0, y0, x1, y0, fill=COLOR_GRID,
                                tags=tag)

    def _draw_number(self, box: Tuple[int, int, int, int], tag: str,
                     value: int) -> None:
        x0, y0, x1, y1 = box
        self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2 + 1,
                                text=str(value), font=NUMBER_FONT,
                                fill=NUMBER_COLORS[value], tags=tag)

    def _draw_mine(self, box: Tuple[int, int, int, int], tag: str) -> None:
        """Мина: чёрный шар с шипами и бликом."""
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        r = self.size * 0.26
        spike = self.size * 0.38
        diag = spike * 0.72
        c = self.canvas
        for dx, dy in ((spike, 0), (0, spike), (diag, diag), (diag, -diag)):
            c.create_line(cx - dx, cy - dy, cx + dx, cy + dy,
                          fill=COLOR_MINE, width=2, tags=tag)
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=COLOR_MINE,
                      width=0, tags=tag)
        h = r * 0.35
        c.create_rectangle(cx - r * 0.55, cy - r * 0.55, cx - r * 0.55 + h,
                           cy - r * 0.55 + h, fill=COLOR_LIGHT, width=0,
                           tags=tag)

    def _draw_flag(self, box: Tuple[int, int, int, int], tag: str) -> None:
        """Флажок: красное полотнище на чёрном древке с подставкой."""
        x0, y0, _, _ = box
        s = self.size
        c = self.canvas
        pole_x = x0 + s * 0.6
        c.create_polygon(pole_x, y0 + s * 0.14, pole_x, y0 + s * 0.52,
                         x0 + s * 0.16, y0 + s * 0.33, fill=COLOR_FLAG,
                         tags=tag)
        c.create_line(pole_x, y0 + s * 0.14, pole_x, y0 + s * 0.7,
                      fill=COLOR_MINE, width=2, tags=tag)
        # Двухступенчатая подставка древка.
        c.create_rectangle(x0 + s * 0.46, y0 + s * 0.64, x0 + s * 0.74,
                           y0 + s * 0.71, fill=COLOR_MINE, width=0,
                           tags=tag)
        c.create_rectangle(x0 + s * 0.3, y0 + s * 0.71, x0 + s * 0.86,
                           y0 + s * 0.8, fill=COLOR_MINE, width=0,
                           tags=tag)

    def _draw_question(self, box: Tuple[int, int, int, int],
                       tag: str) -> None:
        x0, y0, x1, y1 = box
        self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2 + 1, text="?",
                                font=NUMBER_FONT, fill=COLOR_MINE, tags=tag)

    def _draw_cross(self, box: Tuple[int, int, int, int], tag: str) -> None:
        """Красный крест поверх мины — флажок стоял неверно."""
        x0, y0, x1, y1 = box
        m = self.size * 0.18
        for line in ((x0 + m, y0 + m, x1 - m, y1 - m),
                     (x0 + m, y1 - m, x1 - m, y0 + m)):
            self.canvas.create_line(*line, fill=COLOR_CROSS, width=3,
                                    tags=tag)
