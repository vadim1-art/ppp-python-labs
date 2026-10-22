"""Панель управления: слайдеры параметров, выбор палитры и кнопки."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, Tuple

from src.config import (ACCENT_COLOR, ANGLE_RANGE, DEPTH_RANGE,
                        MUTED_TEXT_COLOR, PANEL_COLOR, RATIO_RANGE,
                        TEXT_COLOR, TROUGH_COLOR, UI_FONT, UI_FONT_BOLD)

HINT_TEXT = ("Пробел — анимация угла   ←/→ — угол   ↑/↓ — коэффициент   "
             "+/− — глубина   G — вырастить заново   R — сброс   "
             "Esc — выход")

SLIDER_STYLE = "Tree.Horizontal.TScale"


def _setup_styles(master: tk.Misc) -> None:
    """Настроить внешний вид ttk-слайдеров под тёмную тему."""
    style = ttk.Style(master)
    # Тема «clam» позволяет менять цвета ползунка и жёлоба на всех ОС.
    style.theme_use("clam")
    style.configure(SLIDER_STYLE, background=ACCENT_COLOR,
                    troughcolor=TROUGH_COLOR, bordercolor=PANEL_COLOR,
                    lightcolor=ACCENT_COLOR, darkcolor=ACCENT_COLOR)
    style.map(SLIDER_STYLE, background=[("active", TEXT_COLOR)])


class Slider(tk.Frame):
    """Слайдер с подписью и текущим значением.

    Значение округляется до шага step, а функция on_change вызывается
    только тогда, когда округлённое значение действительно изменилось.
    Программная установка через ``set`` обработчик не вызывает.
    """

    def __init__(self, master: tk.Misc, title: str,
                 bounds: Tuple[float, float], step: float, fmt: str,
                 on_change: Callable[[float], None]) -> None:
        """Создать подпись, поле значения и сам слайдер."""
        super().__init__(master, bg=PANEL_COLOR)
        self._step = step
        self._fmt = fmt
        self._on_change = on_change
        self._value = bounds[0]

        tk.Label(self, text=title, bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=UI_FONT).grid(row=0, column=0, sticky="w")
        self._value_label = tk.Label(self, bg=PANEL_COLOR, fg=ACCENT_COLOR,
                                     font=UI_FONT_BOLD)
        self._value_label.grid(row=0, column=1, sticky="e")

        self.scale = ttk.Scale(self, from_=bounds[0], to=bounds[1],
                               orient=tk.HORIZONTAL, style=SLIDER_STYLE,
                               command=self._on_move, takefocus=0)
        self.scale.grid(row=1, column=0, columnspan=2, sticky="ew",
                        pady=(2, 0))
        self.columnconfigure(0, weight=1)

    def set(self, value: float) -> None:
        """Установить значение, не вызывая обработчик."""
        self._value = self._round(value)
        self.scale.configure(command="")
        self.scale.set(value)
        self.scale.configure(command=self._on_move)
        self._value_label.configure(text=self._fmt.format(value))

    def _on_move(self, raw: str) -> None:
        value = self._round(float(raw))
        if value != self._value:
            self._value = value
            self._value_label.configure(text=self._fmt.format(value))
            self._on_change(value)

    def _round(self, value: float) -> float:
        return round(round(value / self._step) * self._step, 6)


class ControlPanel(tk.Frame):
    """Нижняя панель приложения.

    Панель не меняет модель напрямую: о действиях пользователя она
    сообщает через функции обратного вызова, переданные в конструктор.
    """

    def __init__(self, master: tk.Misc, *,
                 on_angle: Callable[[float], None],
                 on_ratio: Callable[[float], None],
                 on_depth: Callable[[int], None],
                 on_palette: Callable[[str], None],
                 on_angle_grab: Callable[[], None],
                 on_toggle_sweep: Callable[[], None],
                 on_regrow: Callable[[], None],
                 on_reset: Callable[[], None],
                 palettes: Iterable[str]) -> None:
        """Создать слайдеры и кнопки и связать их с обработчиками."""
        super().__init__(master, bg=PANEL_COLOR, padx=12, pady=10)
        _setup_styles(master)

        sliders = tk.Frame(self, bg=PANEL_COLOR)
        sliders.pack(side=tk.TOP, fill=tk.X)
        sliders.columnconfigure((0, 1, 2), weight=1, uniform="slider")

        self.angle_slider = Slider(sliders, "Угол ветвления", ANGLE_RANGE,
                                   0.5, "{:.1f}°", on_angle)
        self.angle_slider.grid(row=0, column=0, sticky="ew", padx=8)
        # Захват слайдера мышью останавливает автоматическую анимацию угла.
        self.angle_slider.scale.bind("<ButtonPress-1>",
                                     lambda _: on_angle_grab(), add="+")

        self.ratio_slider = Slider(sliders, "Коэффициент длины k",
                                   RATIO_RANGE, 0.01, "{:.2f}", on_ratio)
        self.ratio_slider.grid(row=0, column=1, sticky="ew", padx=8)

        self.depth_slider = Slider(sliders, "Глубина рекурсии", DEPTH_RANGE,
                                   1, "{:.0f}", lambda v: on_depth(int(v)))
        self.depth_slider.grid(row=0, column=2, sticky="ew", padx=8)

        buttons = tk.Frame(self, bg=PANEL_COLOR)
        buttons.pack(side=tk.TOP, fill=tk.X, pady=(10, 0))

        self.sweep_button = self._make_button(buttons, "", on_toggle_sweep)
        self.sweep_button.pack(side=tk.LEFT, padx=8)
        self._make_button(buttons, "Вырастить заново", on_regrow).pack(
            side=tk.LEFT, padx=(0, 8))
        self._make_button(buttons, "Сброс", on_reset).pack(side=tk.LEFT)

        tk.Label(buttons, text="Палитра:", bg=PANEL_COLOR, fg=TEXT_COLOR,
                 font=UI_FONT).pack(side=tk.LEFT, padx=(20, 4))
        self.palette_var = tk.StringVar()
        menu = tk.OptionMenu(buttons, self.palette_var, *palettes,
                             command=lambda name: on_palette(str(name)))
        menu.configure(bg=TROUGH_COLOR, fg=TEXT_COLOR, font=UI_FONT,
                       activebackground=ACCENT_COLOR, highlightthickness=0,
                       relief=tk.FLAT, bd=0, width=8, takefocus=0)
        menu["menu"].configure(bg=TROUGH_COLOR, fg=TEXT_COLOR, font=UI_FONT,
                               activebackground=ACCENT_COLOR)
        menu.pack(side=tk.LEFT)

        hint = tk.Label(self, text=HINT_TEXT, bg=PANEL_COLOR,
                        fg=MUTED_TEXT_COLOR, font=UI_FONT, justify=tk.LEFT)
        hint.pack(side=tk.TOP, anchor="w", padx=8, pady=(10, 0))
        # В узком окне подсказка переносится на следующую строку.
        self.bind("<Configure>", lambda e: hint.configure(
            wraplength=max(200, e.width - 40)))
        self.set_sweeping(False)

    def set_values(self, angle: float, ratio: float, depth: int,
                   palette: str) -> None:
        """Показать на слайдерах текущие значения параметров."""
        self.angle_slider.set(angle)
        self.ratio_slider.set(ratio)
        self.depth_slider.set(depth)
        self.palette_var.set(palette)

    def set_sweeping(self, sweeping: bool) -> None:
        """Обновить подпись кнопки анимации угла."""
        self.sweep_button.configure(
            text="❚❚  Пауза" if sweeping else "▶  Анимация угла")

    @staticmethod
    def _make_button(master: tk.Misc, text: str,
                     command: Callable[[], None]) -> tk.Button:
        """Создать плоскую кнопку в стиле приложения."""
        return tk.Button(
            master, text=text, command=command, bg=TROUGH_COLOR,
            fg=TEXT_COLOR, activebackground=ACCENT_COLOR,
            activeforeground=PANEL_COLOR, relief=tk.FLAT, bd=0,
            padx=12, pady=4, font=UI_FONT, cursor="hand2", takefocus=0)
