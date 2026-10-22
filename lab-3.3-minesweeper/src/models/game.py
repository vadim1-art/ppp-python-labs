"""Правила игры «Сапёр»: ходы игрока, таймер, победа и поражение."""

from __future__ import annotations

import random
import time
from enum import Enum
from typing import Callable, Iterable, List, Optional

from src.models.board import Board, Position
from src.models.cell import Cell, Mark
from src.models.difficulty import BEGINNER, Difficulty

MAX_SECONDS = 999  # таймер, как в оригинале, трёхзначный


class GameState(Enum):
    """Состояние партии."""

    READY = "ready"      # мины ещё не расставлены, ждём первый ход
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


class MinesweeperGame:
    """Одна партия «Сапёра».

    Мины расставляются только при первом открытии клетки, поэтому
    первый ход никогда не попадает на мину.
    """

    def __init__(self, difficulty: Difficulty = BEGINNER,
                 rng: Optional[random.Random] = None,
                 clock: Callable[[], float] = time.monotonic,
                 question_marks: bool = True) -> None:
        """Создать игру.

        rng и clock можно подменить в тестах, чтобы расстановка мин
        и время были предсказуемыми.
        """
        self._rng = rng or random.Random()
        self._clock = clock
        self.question_marks = question_marks
        self.new_game(difficulty)

    # ---------------------------------------------------------------
    # Состояние
    # ---------------------------------------------------------------

    def new_game(self, difficulty: Optional[Difficulty] = None) -> None:
        """Начать новую партию (по умолчанию — того же уровня)."""
        if difficulty is not None:
            self.difficulty = difficulty
        self.board = Board(self.difficulty.rows, self.difficulty.cols)
        self.state = GameState.READY
        self.exploded: Optional[Cell] = None
        self._started_at: Optional[float] = None
        self._finished_at: Optional[float] = None

    @property
    def is_over(self) -> bool:
        """Закончена ли партия (победой или поражением)."""
        return self.state in (GameState.WON, GameState.LOST)

    @property
    def mines_left(self) -> int:
        """Мины минус флажки — число на левом счётчике (бывает < 0)."""
        return self.difficulty.mines - self.board.flag_count

    @property
    def elapsed(self) -> int:
        """Сколько целых секунд идёт партия (не больше 999)."""
        if self._started_at is None:
            return 0
        end = (self._finished_at if self._finished_at is not None
               else self._clock())
        return min(MAX_SECONDS, int(end - self._started_at))

    # ---------------------------------------------------------------
    # Ходы игрока
    # ---------------------------------------------------------------

    def reveal(self, row: int, col: int) -> List[Cell]:
        """Открыть клетку (левый клик). Возвращает открытые клетки."""
        if self.is_over:
            return []
        cell = self.board.cell(row, col)
        if cell.is_open or cell.is_flagged:
            return []
        if self.state is GameState.READY:
            self._start((row, col))
        if cell.is_mine:
            self._explode(cell)
            return [cell]
        opened = self.board.open_area(row, col)
        self._check_win()
        return opened

    def chord(self, row: int, col: int) -> List[Cell]:
        """Открыть всех соседей открытой цифры («аккорд»).

        Срабатывает, только если вокруг цифры стоит ровно столько
        флажков, сколько она показывает. Если какой-то флажок стоит
        неверно, открывается мина и игра проиграна.
        """
        if self.state is not GameState.PLAYING:
            return []
        cell = self.board.cell(row, col)
        if not cell.is_open or cell.adjacent == 0:
            return []
        neighbors = list(self.board.neighbors(row, col))
        if sum(n.is_flagged for n in neighbors) != cell.adjacent:
            return []

        opened: List[Cell] = []
        for neighbor in neighbors:
            if neighbor.is_open or neighbor.is_flagged:
                continue
            if neighbor.is_mine:
                self._explode(neighbor)
                opened.append(neighbor)
                return opened
            opened.extend(self.board.open_area(neighbor.row, neighbor.col))
        self._check_win()
        return opened

    def toggle_mark(self, row: int, col: int) -> Mark:
        """Сменить пометку закрытой клетки (правый клик).

        Цикл: пусто → флажок → «?» → пусто. Если знаки вопроса
        отключены, флажок просто ставится и снимается.
        """
        cell = self.board.cell(row, col)
        if self.is_over or cell.is_open:
            return cell.mark
        if cell.mark is Mark.NONE:
            cell.mark = Mark.FLAG
        elif cell.mark is Mark.FLAG and self.question_marks:
            cell.mark = Mark.QUESTION
        else:
            cell.mark = Mark.NONE
        return cell.mark

    def set_question_marks(self, enabled: bool) -> List[Cell]:
        """Включить/выключить знаки «?». Возвращает очищенные клетки."""
        self.question_marks = enabled
        cleared = []
        if not enabled:
            for cell in self.board:
                if cell.mark is Mark.QUESTION:
                    cell.mark = Mark.NONE
                    cleared.append(cell)
        return cleared

    def load_layout(self, mines: Iterable[Position]) -> None:
        """Начать партию с заранее заданными минами (для тестов)."""
        self.new_game()
        self.board.set_mines(mines)
        self.state = GameState.PLAYING
        self._started_at = self._clock()

    # ---------------------------------------------------------------
    # Внутренняя логика
    # ---------------------------------------------------------------

    def _start(self, first_move: Position) -> None:
        self.board.place_random_mines(self.difficulty.mines,
                                      safe=first_move, rng=self._rng)
        self.state = GameState.PLAYING
        self._started_at = self._clock()

    def _finish(self, state: GameState) -> None:
        self.state = state
        self._finished_at = self._clock()

    def _explode(self, cell: Cell) -> None:
        cell.is_open = True
        self.exploded = cell
        self._finish(GameState.LOST)

    def _check_win(self) -> None:
        """Победа — когда открыты все клетки без мин."""
        if self.state is GameState.PLAYING and \
                self.board.closed_safe_count == 0:
            # Как в оригинале, после победы все мины помечаются флажками.
            for cell in self.board:
                if cell.is_mine:
                    cell.mark = Mark.FLAG
            self._finish(GameState.WON)
