"""Главное окно игры «Сапёр»: меню, обработка мыши и таймер."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import List, Optional, Set, Tuple

from src.config import (COLOR_FACE, FRAME_PADDING, HUD_HEIGHT, RECORDS_FILE,
                        TIMER_TICK_MS, WIN_MESSAGE_DELAY_MS, WINDOW_TITLE)
from src.models.cell import Cell
from src.models.difficulty import BEGINNER, PRESETS, Difficulty
from src.models.game import GameState, MinesweeperGame
from src.models.records import RecordsTable
from src.renderers.board_renderer import BoardRenderer
from src.renderers.hud_renderer import Face, HudRenderer
from src.widgets.dialogs import CustomFieldDialog, RecordsDialog, show_rules

ABOUT_TEXT = """\
Сапёр — лабораторная работа 3.3 «Простые игры».
Дисциплина: Практикум по программированию.

Автор: Готовец Вадим Евгеньевич, группа ПИ25-1.

Python 3 + tkinter, вся графика нарисована примитивами холста."""


class MinesweeperApp:
    """Окно игры: связывает модель, отрисовщики и действия игрока."""

    def __init__(self, records_path: Path = RECORDS_FILE) -> None:
        """Создать окно, меню, игровое поле и верхнюю панель."""
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_FACE)

        self.game = MinesweeperGame(BEGINNER)
        self.records = RecordsTable(records_path)
        self._game_id = 0              # растёт с каждой новой партией
        self._pressed: Set[Cell] = set()
        self._left_down = False        # зажата ли левая кнопка над полем
        self._face_down = False        # зажата ли кнопка-смайлик

        self.difficulty_var = tk.StringVar(value=BEGINNER.key)
        self.marks_var = tk.BooleanVar(value=self.game.question_marks)
        self._build_menu()
        self._build_layout()

        self.hud = HudRenderer(self.hud_canvas)
        self.renderer = BoardRenderer(self.board_canvas, self.game)
        self._bind_events()
        self.new_game()

    def run(self) -> None:
        """Запустить главный цикл приложения."""
        self.root.after(TIMER_TICK_MS, self._tick_timer)
        self.root.mainloop()

    def new_game(self, difficulty: Optional[Difficulty] = None) -> None:
        """Начать новую партию (по умолчанию — того же уровня)."""
        self.game.new_game(difficulty)
        self._game_id += 1
        self._pressed.clear()
        self._left_down = False
        self.renderer.draw_board()
        self.hud.layout(self.renderer.pixel_size[0])
        self.difficulty_var.set(self.game.difficulty.key)
        self._update_hud()

    # ---------------------------------------------------------------
    # Построение интерфейса
    # ---------------------------------------------------------------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        game_menu = tk.Menu(menubar, tearoff=False)
        game_menu.add_command(label="Новая игра", accelerator="F2",
                              command=self.new_game)
        game_menu.add_separator()
        for number, level in enumerate(PRESETS, start=1):
            game_menu.add_radiobutton(
                label=level.label, accelerator=str(number),
                variable=self.difficulty_var, value=level.key,
                command=lambda lvl=level: self.new_game(lvl))
        game_menu.add_radiobutton(label="Особое поле…",
                                  variable=self.difficulty_var,
                                  value="custom", command=self._ask_custom)
        game_menu.add_separator()
        game_menu.add_checkbutton(label="Отметки (?)",
                                  variable=self.marks_var,
                                  command=self._toggle_marks)
        game_menu.add_command(label="Рекорды…", command=self._show_records)
        game_menu.add_separator()
        game_menu.add_command(label="Выход", command=self.root.destroy)
        menubar.add_cascade(label="Игра", menu=game_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Правила игры", accelerator="F1",
                              command=lambda: show_rules(self.root))
        help_menu.add_command(label="О программе", command=lambda:
                              messagebox.showinfo("О программе", ABOUT_TEXT,
                                                  parent=self.root))
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.configure(menu=menubar)

    def _build_layout(self) -> None:
        """Классическая рамка: панель со счётчиками сверху, поле снизу."""
        outer = tk.Frame(self.root, bg=COLOR_FACE, bd=3, relief=tk.RAISED,
                         padx=FRAME_PADDING, pady=FRAME_PADDING)
        outer.pack()

        hud_frame = tk.Frame(outer, bg=COLOR_FACE, bd=2, relief=tk.SUNKEN)
        hud_frame.pack(fill=tk.X)
        self.hud_canvas = tk.Canvas(hud_frame, height=HUD_HEIGHT,
                                    bg=COLOR_FACE, highlightthickness=0)
        self.hud_canvas.pack()

        board_frame = tk.Frame(outer, bg=COLOR_FACE, bd=3, relief=tk.SUNKEN)
        board_frame.pack(pady=(FRAME_PADDING, 0))
        self.board_canvas = tk.Canvas(board_frame, bg=COLOR_FACE,
                                      highlightthickness=0, bd=0,
                                      cursor="hand2")
        self.board_canvas.pack()

    def _bind_events(self) -> None:
        # На macOS правая кнопка мыши — это Button-2, а средняя — Button-3.
        aqua = self.root.tk.call("tk", "windowingsystem") == "aqua"
        right, middle = ("2", "3") if aqua else ("3", "2")

        board = self.board_canvas
        board.bind("<ButtonPress-1>", self._on_left_press)
        board.bind("<B1-Motion>", self._on_left_drag)
        board.bind("<ButtonRelease-1>", self._on_left_release)
        board.bind(f"<ButtonPress-{right}>", self._on_right_press)
        board.bind(f"<ButtonRelease-{middle}>", self._on_middle_release)

        hud = self.hud_canvas
        hud.bind("<ButtonPress-1>", self._on_face_press)
        hud.bind("<B1-Motion>", self._on_face_drag)
        hud.bind("<ButtonRelease-1>", self._on_face_release)

        self.root.bind("<F2>", lambda _: self.new_game())
        self.root.bind("<F1>", lambda _: show_rules(self.root))
        for number, level in enumerate(PRESETS, start=1):
            self.root.bind(f"<KeyPress-{number}>",
                           lambda _, lvl=level: self.new_game(lvl))

    # ---------------------------------------------------------------
    # Мышь над полем
    # ---------------------------------------------------------------

    def _on_left_press(self, event: tk.Event) -> None:
        if self.game.is_over:
            return
        self._left_down = True
        self.hud.set_face(Face.OH)
        self._press_at(event.x, event.y)

    def _on_left_drag(self, event: tk.Event) -> None:
        if self._left_down:
            self._press_at(event.x, event.y)

    def _on_left_release(self, event: tk.Event) -> None:
        if not self._left_down:
            return
        self._left_down = False
        self._press_at(-1, -1)  # «отжать» все клетки
        position = self.renderer.cell_at(event.x, event.y)
        if position is not None:
            cell = self.game.board.cell(*position)
            # Клик по открытой цифре работает как «аккорд».
            opened = (self.game.chord(*position) if cell.is_open
                      else self.game.reveal(*position))
            self._show_move(opened, position)
        self._update_hud()

    def _on_right_press(self, event: tk.Event) -> None:
        position = self.renderer.cell_at(event.x, event.y)
        if position is None or self._left_down or self.game.is_over:
            return
        self.game.toggle_mark(*position)
        self.renderer.draw_cell(self.game.board.cell(*position))
        self._update_hud()

    def _on_middle_release(self, event: tk.Event) -> None:
        position = self.renderer.cell_at(event.x, event.y)
        if position is not None:
            self._show_move(self.game.chord(*position), position)
            self._update_hud()

    def _press_at(self, x: int, y: int) -> None:
        """Показать «вдавленными» клетки, которые откроет отпускание кнопки.

        Над закрытой клеткой вдавливается она сама, над открытой цифрой —
        её закрытые соседи (подсказка для «аккорда»).
        """
        pressed: Set[Cell] = set()
        position = self.renderer.cell_at(x, y)
        if position is not None:
            cell = self.game.board.cell(*position)
            if not cell.is_open and not cell.is_flagged:
                pressed = {cell}
            elif cell.is_open and cell.adjacent:
                pressed = {n for n in self.game.board.neighbors(*position)
                           if not n.is_open and not n.is_flagged}
        self.renderer.draw_cells(self._pressed - pressed)
        self.renderer.draw_cells(pressed - self._pressed, pressed=True)
        self._pressed = pressed

    def _show_move(self, opened: List[Cell],
                   origin: Tuple[int, int]) -> None:
        """Отрисовать результат хода и обработать конец партии."""
        if self.game.state is GameState.LOST:
            self.renderer.animate_explosion()
            return
        self.renderer.animate_reveal(opened, origin)
        if self.game.state is GameState.WON:
            # После победы на всех минах появляются флажки.
            self.renderer.draw_cells(c for c in self.game.board if c.is_mine)
            game_id = self._game_id
            self.root.after(WIN_MESSAGE_DELAY_MS,
                            lambda: self._announce_win(game_id))

    # ---------------------------------------------------------------
    # Кнопка-смайлик
    # ---------------------------------------------------------------

    def _on_face_press(self, event: tk.Event) -> None:
        if self.hud.face_contains(event.x, event.y):
            self._face_down = True
            self.hud.set_face(Face.SMILE, pressed=True)

    def _on_face_drag(self, event: tk.Event) -> None:
        if self._face_down:
            inside = self.hud.face_contains(event.x, event.y)
            self.hud.set_face(Face.SMILE if inside else self._face(),
                              pressed=inside)

    def _on_face_release(self, event: tk.Event) -> None:
        if not self._face_down:
            return
        self._face_down = False
        if self.hud.face_contains(event.x, event.y):
            self.new_game()
        else:
            self._update_hud()

    # ---------------------------------------------------------------
    # Меню
    # ---------------------------------------------------------------

    def _ask_custom(self) -> None:
        level = CustomFieldDialog.ask(self.root, self.game.difficulty)
        if level is not None:
            self.new_game(level)
        else:  # отмена — возвращаем отметку в меню на текущий уровень
            self.difficulty_var.set(self.game.difficulty.key)

    def _toggle_marks(self) -> None:
        cleared = self.game.set_question_marks(self.marks_var.get())
        self.renderer.draw_cells(cleared)

    def _show_records(self) -> None:
        RecordsDialog(self.root, self.records, self.records.clear).show()

    # ---------------------------------------------------------------
    # Состояние панели и таймер
    # ---------------------------------------------------------------

    def _face(self) -> Face:
        """Выражение смайлика для текущего состояния игры."""
        if self.game.state is GameState.WON:
            return Face.COOL
        if self.game.state is GameState.LOST:
            return Face.DEAD
        return Face.OH if self._left_down else Face.SMILE

    def _update_hud(self) -> None:
        self.hud.set_mines(self.game.mines_left)
        self.hud.set_time(self.game.elapsed)
        self.hud.set_face(self._face())

    def _tick_timer(self) -> None:
        self.hud.set_time(self.game.elapsed)
        self.root.after(TIMER_TICK_MS, self._tick_timer)

    def _announce_win(self, game_id: int) -> None:
        """Сообщить о победе и проверить рекорд."""
        if game_id != self._game_id or self.game.state is not GameState.WON:
            return  # игрок уже начал новую партию
        seconds = self.game.elapsed
        level = self.game.difficulty
        text = f"Поле разминировано за {seconds} с."
        if level.key != "custom" and self.records.submit(level.key, seconds):
            text += f"\n\nНовый рекорд для уровня «{level.title}»!"
        messagebox.showinfo("Победа!", text, parent=self.root)
