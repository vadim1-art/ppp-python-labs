"""Верхняя панель: счётчик мин, кнопка-смайлик и таймер."""

from __future__ import annotations

import tkinter as tk
from enum import Enum
from typing import Dict, List, Tuple

from src.config import (COLOR_FACE, COLOR_LIGHT, COLOR_MINE, COLOR_SHADOW,
                        DISPLAY_BG, FACE_YELLOW, HUD_HEIGHT, SEGMENT_OFF,
                        SEGMENT_ON)

# Какие сегменты горят у каждого символа. Обозначения стандартные:
#
#      a
#    f   b
#      g
#    e   c
#      d
SEGMENTS_OF: Dict[str, str] = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg",
    "9": "abcdfg", "-": "g",
}

DIGIT_WIDTH = 13
DIGIT_HEIGHT = 23
DIGIT_GAP = 2
SEGMENT_WIDTH = 3
DISPLAY_PADDING = 3
FACE_BUTTON = 36


class Face(Enum):
    """Выражения смайлика."""

    SMILE = "smile"   # обычная игра
    OH = "oh"         # зажата кнопка мыши над полем
    DEAD = "dead"     # проигрыш
    COOL = "cool"     # победа


def format_counter(value: int) -> str:
    """Перевести число в три символа индикатора: 7 → «007», -5 → «-05».

    Значение ограничивается диапазоном -99..999.
    """
    value = max(-99, min(999, value))
    if value < 0:
        return f"-{abs(value):02d}"
    return f"{value:03d}"


def segment_polygons(x: float, y: float) -> Dict[str, List[float]]:
    """Координаты шестиугольных сегментов цифры с левым верхним углом (x, y).

    Каждый сегмент — вытянутый шестиугольник со скошенными концами,
    поэтому соседние сегменты стыкуются «ёлочкой», как на настоящем
    индикаторе.
    """
    w, h, t = DIGIT_WIDTH, DIGIT_HEIGHT, SEGMENT_WIDTH
    half = t / 2
    mid = y + h / 2

    def horizontal(cy: float) -> List[float]:
        return [x + 1, cy, x + 1 + half, cy - half, x + w - 1 - half,
                cy - half, x + w - 1, cy, x + w - 1 - half, cy + half,
                x + 1 + half, cy + half]

    def vertical(cx: float, top: float, bottom: float) -> List[float]:
        return [cx, top, cx + half, top + half, cx + half, bottom - half,
                cx, bottom, cx - half, bottom - half, cx - half, top + half]

    return {
        "a": horizontal(y + half),
        "g": horizontal(mid),
        "d": horizontal(y + h - half),
        "f": vertical(x + half, y + 1, mid - 1),
        "b": vertical(x + w - half, y + 1, mid - 1),
        "e": vertical(x + half, mid + 1, y + h - 1),
        "c": vertical(x + w - half, mid + 1, y + h - 1),
    }


class HudRenderer:
    """Рисует верхнюю панель и сообщает, попал ли клик в смайлик."""

    def __init__(self, canvas: tk.Canvas) -> None:
        """Привязать панель к холсту."""
        self.canvas = canvas
        self.width = 0
        self._values = {"mines": 0, "time": 0}
        self._face = Face.SMILE
        self._face_pressed = False

    def layout(self, width: int) -> None:
        """Разместить элементы панели по ширине поля и перерисовать."""
        self.width = width
        self.canvas.configure(width=width, height=HUD_HEIGHT)
        self.canvas.delete("all")
        self._draw_display("mines")
        self._draw_display("time")
        self._draw_face()

    def set_mines(self, value: int) -> None:
        """Показать число оставшихся мин."""
        self._set_value("mines", value)

    def set_time(self, value: int) -> None:
        """Показать прошедшее время в секундах."""
        self._set_value("time", value)

    def set_face(self, face: Face, pressed: bool = False) -> None:
        """Сменить выражение смайлика или вдавить кнопку."""
        if (face, pressed) != (self._face, self._face_pressed):
            self._face, self._face_pressed = face, pressed
            self._draw_face()

    def face_contains(self, x: int, y: int) -> bool:
        """Попадает ли точка (x, y) в кнопку-смайлик."""
        x0, y0, x1, y1 = self._face_box()
        return x0 <= x <= x1 and y0 <= y <= y1

    # ---------------------------------------------------------------

    def _set_value(self, name: str, value: int) -> None:
        if self._values[name] != value:
            self._values[name] = value
            self._draw_display(name)

    def _display_origin(self, name: str) -> Tuple[float, float]:
        width = 3 * DIGIT_WIDTH + 2 * DIGIT_GAP + 2 * DISPLAY_PADDING
        height = DIGIT_HEIGHT + 2 * DISPLAY_PADDING
        y = (HUD_HEIGHT - height) / 2
        x = 8 if name == "mines" else self.width - 8 - width
        return x, y

    def _draw_display(self, name: str) -> None:
        """Нарисовать трёхразрядный семисегментный индикатор."""
        tag = f"display_{name}"
        self.canvas.delete(tag)
        x, y = self._display_origin(name)
        width = 3 * DIGIT_WIDTH + 2 * DIGIT_GAP + 2 * DISPLAY_PADDING
        height = DIGIT_HEIGHT + 2 * DISPLAY_PADDING
        self.canvas.create_rectangle(x, y, x + width, y + height,
                                     fill=DISPLAY_BG, outline=COLOR_SHADOW,
                                     tags=tag)
        text = format_counter(self._values[name])
        for index, char in enumerate(text):
            dx = x + DISPLAY_PADDING + index * (DIGIT_WIDTH + DIGIT_GAP)
            lit = SEGMENTS_OF[char]
            for segment, points in segment_polygons(
                    dx, y + DISPLAY_PADDING).items():
                self.canvas.create_polygon(
                    points, fill=SEGMENT_ON if segment in lit
                    else SEGMENT_OFF, tags=tag)

    def _face_box(self) -> Tuple[float, float, float, float]:
        x0 = (self.width - FACE_BUTTON) / 2
        y0 = (HUD_HEIGHT - FACE_BUTTON) / 2
        return x0, y0, x0 + FACE_BUTTON, y0 + FACE_BUTTON

    def _draw_face(self) -> None:
        """Нарисовать кнопку со смайликом."""
        tag = "face"
        c = self.canvas
        c.delete(tag)
        x0, y0, x1, y1 = self._face_box()
        light, dark = ((COLOR_SHADOW, COLOR_LIGHT) if self._face_pressed
                       else (COLOR_LIGHT, COLOR_SHADOW))
        c.create_rectangle(x0, y0, x1, y1, fill=COLOR_FACE,
                           outline=COLOR_SHADOW, tags=tag)
        c.create_line(x0 + 1, y1 - 2, x0 + 1, y0 + 1, x1 - 1, y0 + 1,
                      fill=light, width=3, tags=tag)
        c.create_line(x1 - 1, y0 + 2, x1 - 1, y1 - 1, x0 + 2, y1 - 1,
                      fill=dark, width=3, tags=tag)

        # Вдавленная кнопка рисуется со сдвигом на пиксель.
        shift = 1 if self._face_pressed else 0
        cx, cy = (x0 + x1) / 2 + shift, (y0 + y1) / 2 + shift
        r = 12
        c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=FACE_YELLOW,
                      outline=COLOR_MINE, width=1.5, tags=tag)
        self._draw_eyes(cx, cy, tag)
        self._draw_mouth(cx, cy, tag)

    def _draw_eyes(self, cx: float, cy: float, tag: str) -> None:
        c = self.canvas
        if self._face is Face.DEAD:
            for ex in (cx - 5, cx + 5):  # глаза-крестики
                c.create_line(ex - 2.5, cy - 6.5, ex + 2.5, cy - 1.5,
                              fill=COLOR_MINE, width=1.5, tags=tag)
                c.create_line(ex - 2.5, cy - 1.5, ex + 2.5, cy - 6.5,
                              fill=COLOR_MINE, width=1.5, tags=tag)
        elif self._face is Face.COOL:
            # Солнцезащитные очки: две линзы и перемычка.
            c.create_line(cx - 11, cy - 5, cx + 11, cy - 5,
                          fill=COLOR_MINE, width=1.5, tags=tag)
            for ex in (cx - 5, cx + 5):
                c.create_polygon(ex - 4.5, cy - 6, ex + 4.5, cy - 6,
                                 ex + 3, cy - 1, ex - 3, cy - 1,
                                 fill=COLOR_MINE, tags=tag)
        else:
            for ex in (cx - 4.5, cx + 4.5):
                c.create_oval(ex - 1.8, cy - 6, ex + 1.8, cy - 2.4,
                              fill=COLOR_MINE, width=0, tags=tag)

    def _draw_mouth(self, cx: float, cy: float, tag: str) -> None:
        c = self.canvas
        if self._face is Face.OH:
            c.create_oval(cx - 3, cy + 2, cx + 3, cy + 8, outline=COLOR_MINE,
                          width=1.5, tags=tag)
        elif self._face is Face.DEAD:
            c.create_arc(cx - 6, cy + 3, cx + 6, cy + 12, start=20,
                         extent=140, style=tk.ARC, outline=COLOR_MINE,
                         width=1.5, tags=tag)
        else:
            c.create_arc(cx - 7, cy - 4, cx + 7, cy + 8, start=200,
                         extent=140, style=tk.ARC, outline=COLOR_MINE,
                         width=1.5, tags=tag)
