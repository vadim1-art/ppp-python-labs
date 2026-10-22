"""Отрисовка фрактального дерева на холсте tkinter."""

from __future__ import annotations

import colorsys
import tkinter as tk
from typing import Callable, Dict, List, Sequence, Tuple

from src.config import CANVAS_MARGIN, MAX_LINE_WIDTH, TRUNK_FRACTION
from src.models.tree_model import Segment, bounding_box

RGB = Tuple[int, int, int]


def _lerp_color(start: RGB, end: RGB, t: float) -> str:
    """Линейно смешать два цвета и вернуть результат в формате #rrggbb."""
    r, g, b = (round(a + (b - a) * t) for a, b in zip(start, end))
    return f"#{r:02x}{g:02x}{b:02x}"


def _gradient(start: RGB, end: RGB) -> Callable[[float], str]:
    """Палитра-градиент: цвет плавно меняется от ствола к листьям."""
    return lambda t: _lerp_color(start, end, t)


def _rainbow(t: float) -> str:
    """Палитра-радуга: тон (hue) зависит от уровня ветви."""
    r, g, b = colorsys.hsv_to_rgb(0.02 + 0.75 * t, 0.65, 1.0)
    return f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"


# Каждая палитра — функция t -> цвет, где t = 0 у ствола и 1 у листьев.
PALETTES: Dict[str, Callable[[float], str]] = {
    "Белый": _gradient((255, 255, 255), (255, 255, 255)),
    "Дерево": _gradient((120, 78, 44), (126, 217, 87)),
    "Сакура": _gradient((104, 66, 52), (255, 168, 207)),
    "Осень": _gradient((96, 58, 34), (255, 176, 46)),
    "Неон": _gradient((122, 162, 247), (247, 118, 142)),
    "Радуга": _rainbow,
}


class TreeRenderer:
    """Рисует список отрезков на холсте, вписывая дерево в окно.

    Чтобы анимация была плавной, линии не пересоздаются на каждом кадре:
    если число отрезков и стиль не изменились, у уже существующих линий
    обновляются только координаты.
    """

    def __init__(self, canvas: tk.Canvas, palette: str) -> None:
        """Привязать отрисовщик к холсту и выбрать палитру."""
        self.canvas = canvas
        self.palette = palette
        self._items: List[int] = []
        self._style_key: Tuple[str, int] = ("", 0)

    @property
    def palette(self) -> str:
        """Название текущей палитры (ключ словаря PALETTES)."""
        return self._palette

    @palette.setter
    def palette(self, name: str) -> None:
        if name not in PALETTES:
            raise ValueError(f"Неизвестная палитра: {name}")
        self._palette = name

    def render(self, segments: Sequence[Segment], depth: int) -> None:
        """Нарисовать отрезки дерева глубины depth."""
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        scale, base_x, base_y = self._fit(segments, width, height)

        def to_screen(x: float, y: float) -> Tuple[float, float]:
            # Мировая ось Y направлена вверх, экранная — вниз.
            return base_x + x * scale, base_y - y * scale

        coords = [(*to_screen(s.x1, s.y1), *to_screen(s.x2, s.y2))
                  for s in segments]

        style_key = (self.palette, depth)
        if len(coords) != len(self._items) or style_key != self._style_key:
            self._recreate(segments, coords, depth)
            self._style_key = style_key
        else:
            for item, xy in zip(self._items, coords):
                self.canvas.coords(item, *xy)

    def clear(self) -> None:
        """Удалить с холста все линии дерева."""
        for item in self._items:
            self.canvas.delete(item)
        self._items = []

    def _recreate(self, segments: Sequence[Segment],
                  coords: Sequence[Tuple[float, float, float, float]],
                  depth: int) -> None:
        """Пересоздать все линии (меняется число ветвей или палитра)."""
        self.clear()
        color_of = PALETTES[self.palette]
        # Цвет и толщина зависят только от уровня — считаем их один раз.
        styles = [self._style(level, depth, color_of)
                  for level in range(depth)]
        for segment, xy in zip(segments, coords):
            color, width = styles[segment.level]
            self._items.append(self.canvas.create_line(
                *xy, fill=color, width=width, capstyle=tk.ROUND))

    @staticmethod
    def _style(level: int, depth: int,
               color_of: Callable[[float], str]) -> Tuple[str, float]:
        """Цвет и толщина линии для ветви уровня level."""
        t = level / (depth - 1) if depth > 1 else 0.0
        width = 1.0 + (MAX_LINE_WIDTH - 1.0) * (1.0 - t) ** 2
        return color_of(t), width

    @staticmethod
    def _fit(segments: Sequence[Segment], width: int,
             height: int) -> Tuple[float, float, float]:
        """Подобрать масштаб и положение основания ствола на холсте.

        Базовый масштаб задаёт длину ствола (TRUNK_FRACTION от высоты
        окна). Если крона не помещается в окно, масштаб уменьшается.
        Возвращает (масштаб, x основания, y основания) в пикселях.
        """
        min_x, min_y, max_x, max_y = bounding_box(segments)
        scale = TRUNK_FRACTION * height

        half_width = max(abs(min_x), abs(max_x))
        if half_width > 0:
            scale = min(scale, (width / 2 - CANVAS_MARGIN) / half_width)

        # При углах больше 90° ветви могут опускаться ниже основания.
        below = max(0.0, -min_y)
        full_height = max_y + below
        if full_height > 0:
            scale = min(scale, (height - 2 * CANVAS_MARGIN) / full_height)

        base_x = width / 2
        base_y = height - CANVAS_MARGIN - below * scale
        return scale, base_x, base_y
