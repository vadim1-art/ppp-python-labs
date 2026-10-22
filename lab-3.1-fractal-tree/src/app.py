"""Главное окно приложения и главный цикл анимации."""

from __future__ import annotations

import tkinter as tk

from src.config import (ANGLE_RANGE, BACKGROUND_COLOR, CANVAS_HEIGHT,
                        CANVAS_WIDTH, DEFAULT_ANGLE, DEFAULT_DEPTH,
                        DEFAULT_PALETTE, DEFAULT_RATIO, DEPTH_RANGE,
                        FRAME_DELAY_MS, GROWTH_SPEED, MIN_WINDOW_SIZE,
                        MUTED_TEXT_COLOR, PANEL_COLOR, RATIO_RANGE,
                        SWEEP_SPEED, UI_FONT, WINDOW_TITLE)
from src.models.tree_model import FractalTree, grow_stage
from src.renderers.tree_renderer import PALETTES, TreeRenderer
from src.widgets.controls import ControlPanel

# Клавиши с латинскими буквами дублируются для русской раскладки.
REGROW_KEYS = ("g", "G", "Cyrillic_pe", "Cyrillic_PE")
RESET_KEYS = ("r", "R", "Cyrillic_ka", "Cyrillic_KA")


def _clamp(value: float, bounds: tuple) -> float:
    """Ограничить значение диапазоном bounds = (минимум, максимум)."""
    return max(bounds[0], min(bounds[1], value))


class FractalTreeApp:
    """Связывает модель дерева, отрисовщик и панель управления.

    Главный цикл реализован через ``after``: каждые FRAME_DELAY_MS
    миллисекунд вызывается ``_tick``, который продвигает анимации
    (рост дерева и автоматическое изменение угла) и перерисовывает
    холст, только если что-то изменилось.
    """

    def __init__(self) -> None:
        """Создать окно, модель и элементы управления."""
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.configure(bg=PANEL_COLOR)
        self.root.minsize(*MIN_WINDOW_SIZE)

        self.tree = FractalTree(DEFAULT_ANGLE, DEFAULT_RATIO, DEFAULT_DEPTH)
        self._segments = self.tree.build()
        self._growth = 0.0        # сколько уровней дерева уже «выросло»
        self._sweeping = False    # включена ли анимация угла
        self._sweep_direction = 1
        self._dirty = True        # нужно ли перерисовать кадр

        self.controls = ControlPanel(
            self.root,
            on_angle=self._on_angle_slider,
            on_ratio=self._on_ratio_slider,
            on_depth=self._on_depth_slider,
            on_palette=self._on_palette,
            on_angle_grab=lambda: self._set_sweeping(False),
            on_toggle_sweep=self.toggle_sweep,
            on_regrow=self.regrow,
            on_reset=self.reset,
            palettes=PALETTES.keys(),
        )
        # Панель упаковывается первой, чтобы при уменьшении окна
        # сжимался холст, а не элементы управления.
        self.controls.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self.root, width=CANVAS_WIDTH,
                                height=CANVAS_HEIGHT, bg=BACKGROUND_COLOR,
                                highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _: self._mark_dirty())
        # Строка состояния выводится прямо на холсте, в левом верхнем углу.
        self._info = self.canvas.create_text(
            14, 12, anchor="nw", fill=MUTED_TEXT_COLOR, font=UI_FONT)

        self.renderer = TreeRenderer(self.canvas, DEFAULT_PALETTE)
        self._sync_controls()
        self._bind_keys()

    def run(self) -> None:
        """Запустить главный цикл приложения."""
        self.root.after(FRAME_DELAY_MS, self._tick)
        self.root.mainloop()

    # ---------------------------------------------------------------
    # Действия пользователя
    # ---------------------------------------------------------------

    def toggle_sweep(self) -> None:
        """Включить или поставить на паузу анимацию угла ветвления."""
        self._set_sweeping(not self._sweeping)

    def regrow(self) -> None:
        """Запустить анимацию роста дерева с самого ствола."""
        self._growth = 0.0
        self._mark_dirty()

    def reset(self) -> None:
        """Вернуть параметры по умолчанию и вырастить дерево заново."""
        self._set_sweeping(False)
        self.tree.angle = DEFAULT_ANGLE
        self.tree.ratio = DEFAULT_RATIO
        self.tree.depth = DEFAULT_DEPTH
        self.renderer.palette = DEFAULT_PALETTE
        self._rebuild()
        self._sync_controls()
        self.regrow()

    def change_angle(self, delta: float) -> None:
        """Изменить угол на delta градусов (с клавиатуры)."""
        self._set_sweeping(False)
        self._set_angle(_clamp(self.tree.angle + delta, ANGLE_RANGE))

    def change_ratio(self, delta: float) -> None:
        """Изменить коэффициент убывания длины на delta."""
        self.tree.ratio = round(_clamp(self.tree.ratio + delta,
                                       RATIO_RANGE), 2)
        self._rebuild()
        self._sync_controls()

    def change_depth(self, delta: int) -> None:
        """Изменить глубину рекурсии на delta уровней."""
        self._set_depth(int(_clamp(self.tree.depth + delta, DEPTH_RANGE)))
        self._sync_controls()

    # ---------------------------------------------------------------
    # Обработчики панели управления
    # ---------------------------------------------------------------

    def _on_angle_slider(self, value: float) -> None:
        self._set_angle(value)

    def _on_ratio_slider(self, value: float) -> None:
        self.tree.ratio = value
        self._rebuild()

    def _on_depth_slider(self, value: int) -> None:
        if value != self.tree.depth:
            self._set_depth(value)

    def _on_palette(self, name: str) -> None:
        self.renderer.palette = name
        self._mark_dirty()

    # ---------------------------------------------------------------
    # Внутренняя логика
    # ---------------------------------------------------------------

    def _tick(self) -> None:
        """Один кадр главного цикла: шаг анимаций и перерисовка."""
        if self._growth < self.tree.depth:
            self._growth = min(float(self.tree.depth),
                               self._growth + GROWTH_SPEED)
            self._dirty = True

        if self._sweeping:
            angle = self.tree.angle + self._sweep_direction * SWEEP_SPEED
            # Дойдя до края диапазона, угол начинает меняться в обратную
            # сторону — фигуры плавно перетекают туда и обратно.
            if not ANGLE_RANGE[0] <= angle <= ANGLE_RANGE[1]:
                self._sweep_direction = -self._sweep_direction
                angle = _clamp(angle, ANGLE_RANGE)
            self._set_angle(angle)
            self.controls.angle_slider.set(angle)

        if self._dirty:
            self._redraw()
        self.root.after(FRAME_DELAY_MS, self._tick)

    def _redraw(self) -> None:
        """Перерисовать дерево с учётом анимации роста."""
        self._dirty = False
        visible = grow_stage(self._segments, self._growth)
        self.renderer.render(visible, self.tree.depth)
        self.canvas.itemconfigure(
            self._info,
            text=f"Ветвей: {len(visible)} из {self.tree.segment_count}\n"
                 f"Угол: {self.tree.angle:.1f}°\n"
                 f"k = {self.tree.ratio:.2f}")
        self.canvas.tag_raise(self._info)  # текст поверх веток

    def _set_angle(self, angle: float) -> None:
        self.tree.angle = angle
        self._rebuild()

    def _set_depth(self, depth: int) -> None:
        self.tree.depth = depth
        # Новые уровни «дорастают» от текущего состояния анимации.
        self._growth = min(self._growth, float(depth))
        self._rebuild()

    def _set_sweeping(self, sweeping: bool) -> None:
        self._sweeping = sweeping
        self.controls.set_sweeping(sweeping)

    def _rebuild(self) -> None:
        """Пересчитать ветви после изменения параметров модели."""
        self._segments = self.tree.build()
        self._mark_dirty()

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _sync_controls(self) -> None:
        """Перенести значения из модели на слайдеры."""
        self.controls.set_values(self.tree.angle, self.tree.ratio,
                                 self.tree.depth, self.renderer.palette)

    def _bind_keys(self) -> None:
        """Назначить горячие клавиши."""
        bindings = {
            "<space>": lambda _: self.toggle_sweep(),
            "<Left>": lambda _: self.change_angle(-1),
            "<Right>": lambda _: self.change_angle(1),
            "<Up>": lambda _: self.change_ratio(0.01),
            "<Down>": lambda _: self.change_ratio(-0.01),
            "<plus>": lambda _: self.change_depth(1),
            "<equal>": lambda _: self.change_depth(1),
            "<KP_Add>": lambda _: self.change_depth(1),
            "<minus>": lambda _: self.change_depth(-1),
            "<KP_Subtract>": lambda _: self.change_depth(-1),
            "<Escape>": lambda _: self.root.destroy(),
        }
        for key in REGROW_KEYS:
            bindings[f"<KeyPress-{key}>"] = lambda _: self.regrow()
        for key in RESET_KEYS:
            bindings[f"<KeyPress-{key}>"] = lambda _: self.reset()
        for sequence, handler in bindings.items():
            self.root.bind(sequence, handler)
