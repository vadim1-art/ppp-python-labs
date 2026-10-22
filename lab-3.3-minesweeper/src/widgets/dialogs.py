"""Диалоговые окна: особое поле, таблица рекордов, правила."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

from src.models.difficulty import (MAX_COLS, MAX_ROWS, MIN_SIDE, PRESETS,
                                   Difficulty, custom, max_mines)
from src.models.records import RecordsTable

RULES_TEXT = """\
Цель — открыть все клетки, в которых нет мин.

• Левый клик — открыть клетку. Первый ход всегда безопасен.
• Цифра показывает, сколько мин среди восьми соседних клеток.
• Если рядом мин нет, вся пустая область открывается сама.
• Правый клик — поставить флажок, затем «?», затем снять отметку.
• Клик по открытой цифре (или средней кнопкой), когда вокруг стоит
  столько же флажков, открывает всех остальных соседей.

Счётчик слева — мины минус флажки, справа — время в секундах.
Смайлик или F2 — новая игра; 1, 2, 3 — смена уровня сложности."""


class _ModalDialog(tk.Toplevel):
    """Базовое модальное окно, привязанное к главному."""

    def __init__(self, master: tk.Misc, title: str) -> None:
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.configure(padx=14, pady=12)
        self.bind("<Escape>", lambda _: self.destroy())

    def show(self) -> None:
        """Показать окно и дождаться его закрытия."""
        try:
            self.wait_visibility()
            self.grab_set()  # блокируем главное окно, пока открыт диалог
        except tk.TclError:
            pass
        self.focus_set()
        self.master.wait_window(self)


class CustomFieldDialog(_ModalDialog):
    """Ввод размеров поля и числа мин для уровня «Особый»."""

    def __init__(self, master: tk.Misc, current: Difficulty) -> None:
        """Создать поля ввода, заполненные параметрами текущей игры."""
        super().__init__(master, "Особое поле")
        self.result: Optional[Difficulty] = None
        self._vars = {}
        fields = (
            ("rows", "Высота (строк):", current.rows, MIN_SIDE, MAX_ROWS),
            ("cols", "Ширина (столбцов):", current.cols, MIN_SIDE, MAX_COLS),
            ("mines", "Число мин:", current.mines, 1,
             max_mines(MAX_ROWS, MAX_COLS)),
        )
        for row, (name, label, value, low, high) in enumerate(fields):
            tk.Label(self, text=label).grid(row=row, column=0, sticky="w",
                                            pady=3)
            var = tk.StringVar(value=str(value))
            tk.Spinbox(self, from_=low, to=high, textvariable=var,
                       width=6).grid(row=row, column=1, padx=(8, 0), pady=3)
            self._vars[name] = var

        buttons = tk.Frame(self)
        buttons.grid(row=len(fields), column=0, columnspan=2, pady=(10, 0))
        tk.Button(buttons, text="OK", width=9, command=self._accept).pack(
            side=tk.LEFT, padx=4)
        tk.Button(buttons, text="Отмена", width=9,
                  command=self.destroy).pack(side=tk.LEFT, padx=4)
        self.bind("<Return>", lambda _: self._accept())

    @classmethod
    def ask(cls, master: tk.Misc,
            current: Difficulty) -> Optional[Difficulty]:
        """Показать диалог и вернуть выбранный уровень или None."""
        dialog = cls(master, current)
        dialog.show()
        return dialog.result

    def _accept(self) -> None:
        try:
            values = {name: int(var.get())
                      for name, var in self._vars.items()}
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целые числа.",
                                 parent=self)
            return
        # Значения вне допустимых границ аккуратно приводятся к ним.
        self.result = custom(values["rows"], values["cols"],
                             values["mines"])
        self.destroy()


class RecordsDialog(_ModalDialog):
    """Таблица лучших результатов по уровням сложности."""

    def __init__(self, master: tk.Misc, records: RecordsTable,
                 on_clear: Callable[[], None]) -> None:
        """Построить таблицу рекордов."""
        super().__init__(master, "Рекорды")
        self._records = records
        self._on_clear = on_clear
        self._table = tk.Frame(self)
        self._table.pack()
        self._fill()
        buttons = tk.Frame(self)
        buttons.pack(pady=(12, 0))
        tk.Button(buttons, text="Сбросить", width=10,
                  command=self._clear).pack(side=tk.LEFT, padx=4)
        tk.Button(buttons, text="OK", width=10,
                  command=self.destroy).pack(side=tk.LEFT, padx=4)

    def _fill(self) -> None:
        for child in self._table.winfo_children():
            child.destroy()
        for column, title in enumerate(("Уровень", "Время", "Дата")):
            tk.Label(self._table, text=title, font=("Helvetica", 10, "bold")
                     ).grid(row=0, column=column, padx=10, sticky="w")
        for row, level in enumerate(PRESETS, start=1):
            best = self._records.best(level.key)
            cells = (level.title,
                     f"{best['time']} с" if best else "—",
                     best.get("date", "") if best else "")
            for column, text in enumerate(cells):
                tk.Label(self._table, text=text).grid(
                    row=row, column=column, padx=10, sticky="w")

    def _clear(self) -> None:
        if messagebox.askyesno("Рекорды", "Удалить все рекорды?",
                               parent=self):
            self._on_clear()
            self._fill()


def show_rules(master: tk.Misc) -> None:
    """Показать краткие правила игры."""
    messagebox.showinfo("Правила игры", RULES_TEXT, parent=master)
