"""Модель фрактального дерева: рекурсивное построение ветвей.

Модель ничего не знает о tkinter и работает в «мировых» координатах:
основание ствола находится в точке (0, 0), ось Y направлена вверх,
длина ствола равна 1. Перевод в пиксели холста выполняет отрисовщик.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Tuple

TRUNK_HEADING = 90.0  # ствол растёт вертикально вверх


@dataclass(frozen=True)
class Segment:
    """Одна ветвь дерева — отрезок от (x1, y1) до (x2, y2).

    Атрибут level — номер итерации: 0 у ствола, 1 у первых двух ветвей
    и так далее.
    """

    x1: float
    y1: float
    x2: float
    y2: float
    level: int

    @property
    def length(self) -> float:
        """Длина отрезка."""
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)

    @property
    def heading(self) -> float:
        """Направление отрезка в градусах (0° — вправо, 90° — вверх)."""
        return math.degrees(math.atan2(self.y2 - self.y1, self.x2 - self.x1))

    def partial(self, fraction: float) -> "Segment":
        """Вернуть начальную часть отрезка длиной fraction от полной."""
        return Segment(
            self.x1,
            self.y1,
            self.x1 + (self.x2 - self.x1) * fraction,
            self.y1 + (self.y2 - self.y1) * fraction,
            self.level,
        )


class FractalTree:
    """Фрактальное дерево с настраиваемым углом, коэффициентом и глубиной.

    Алгоритм: рисуется вертикальный ствол; из его конца выходят две
    ветви, повёрнутые на +angle и -angle и укороченные в ratio раз;
    из конца каждой ветви снова выходят две ветви, и так depth раз.
    """

    def __init__(self, angle: float, ratio: float, depth: int) -> None:
        """Создать дерево с заданными параметрами."""
        self.angle = angle
        self.ratio = ratio
        self.depth = depth

    @property
    def angle(self) -> float:
        """Угол между ветвью и её продолжением, градусы (0..180)."""
        return self._angle

    @angle.setter
    def angle(self, value: float) -> None:
        if not 0.0 <= value <= 180.0:
            raise ValueError("Угол должен быть в диапазоне 0..180°")
        self._angle = float(value)

    @property
    def ratio(self) -> float:
        """Во сколько раз дочерняя ветвь короче родительской (0..1)."""
        return self._ratio

    @ratio.setter
    def ratio(self, value: float) -> None:
        if not 0.0 < value < 1.0:
            raise ValueError("Коэффициент длины должен быть в (0, 1)")
        self._ratio = float(value)

    @property
    def depth(self) -> int:
        """Число итераций (уровней) дерева, не меньше 1."""
        return self._depth

    @depth.setter
    def depth(self, value: int) -> None:
        if int(value) < 1:
            raise ValueError("Глубина рекурсии должна быть не меньше 1")
        self._depth = int(value)

    @property
    def segment_count(self) -> int:
        """Число ветвей полного дерева: 1 + 2 + 4 + ... = 2^depth - 1."""
        return 2 ** self.depth - 1

    def build(self) -> List[Segment]:
        """Построить все ветви дерева.

        Ветви идут в порядке обхода в глубину (родитель раньше потомков),
        поэтому при одинаковой глубине порядок отрезков не меняется —
        это позволяет отрисовщику просто сдвигать уже нарисованные линии.
        """
        segments: List[Segment] = []
        self._grow(0.0, 0.0, TRUNK_HEADING, 1.0, 0, segments)
        return segments

    def _grow(self, x: float, y: float, heading: float, length: float,
              level: int, out: List[Segment]) -> None:
        """Рекурсивно добавить ветвь и всех её потомков в список out."""
        if level >= self.depth:  # условие остановки рекурсии
            return
        # Конец ветви: смещение на length в направлении heading.
        rad = math.radians(heading)
        x2 = x + length * math.cos(rad)
        y2 = y + length * math.sin(rad)
        out.append(Segment(x, y, x2, y2, level))

        child_length = length * self.ratio
        self._grow(x2, y2, heading + self.angle, child_length, level + 1, out)
        self._grow(x2, y2, heading - self.angle, child_length, level + 1, out)


def grow_stage(segments: Iterable[Segment], progress: float) -> List[Segment]:
    """Вернуть «недорисованное» дерево для анимации роста.

    progress — сколько уровней уже выросло: при progress = 2.5 ствол
    и первые ветви нарисованы полностью, а ветви уровня 2 — наполовину.
    Ветви, которые ещё не начали расти, в результат не попадают.
    """
    result = []
    for segment in segments:
        fraction = progress - segment.level
        if fraction <= 0.0:
            continue
        result.append(segment if fraction >= 1.0
                      else segment.partial(fraction))
    return result


def bounding_box(segments: Iterable[Segment]
                 ) -> Tuple[float, float, float, float]:
    """Вернуть границы дерева (min_x, min_y, max_x, max_y).

    Для пустого списка возвращается вырожденный прямоугольник в нуле.
    """
    xs: List[float] = []
    ys: List[float] = []
    for s in segments:
        xs.extend((s.x1, s.x2))
        ys.extend((s.y1, s.y2))
    if not xs:
        return 0.0, 0.0, 0.0, 0.0
    return min(xs), min(ys), max(xs), max(ys)
