"""Тесты правил игры: ходы, флажки, аккорд, победа, поражение, таймер."""

import random
import unittest

from src.models.cell import Mark
from src.models.difficulty import BEGINNER, EXPERT, custom
from src.models.game import GameState, MinesweeperGame


class FakeClock:
    """Управляемые часы для проверки таймера."""

    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def make_game(mines, rows=4, cols=4, **kwargs):
    """Игра на поле rows × cols с минами в заданных клетках."""
    game = MinesweeperGame(custom(5, 5, 1), **kwargs)
    game.difficulty = type(game.difficulty)("test", "Тест", rows, cols,
                                            len(mines))
    game.load_layout(mines)
    return game


class RevealTest(unittest.TestCase):
    """Открытие клеток и завершение партии."""

    def test_first_move_is_always_safe(self):
        for seed in range(30):
            game = MinesweeperGame(EXPERT, rng=random.Random(seed))
            self.assertIs(game.state, GameState.READY)
            opened = game.reveal(8, 15)
            self.assertNotEqual(game.state, GameState.LOST)
            self.assertGreater(len(opened), 1)
            self.assertEqual(game.board.mine_count, 99)

    def test_reveal_mine_loses(self):
        game = make_game([(0, 0)])
        opened = game.reveal(0, 0)
        self.assertIs(game.state, GameState.LOST)
        self.assertIs(game.exploded, game.board.cell(0, 0))
        self.assertEqual(opened, [game.board.cell(0, 0)])

    def test_win_when_all_safe_cells_opened(self):
        game = make_game([(0, 0)])
        game.reveal(3, 3)
        self.assertIs(game.state, GameState.WON)
        self.assertTrue(game.board.cell(0, 0).is_flagged)
        self.assertEqual(game.mines_left, 0)

    def test_no_moves_after_game_over(self):
        game = make_game([(0, 0)])
        game.reveal(0, 0)
        self.assertEqual(game.reveal(3, 3), [])
        self.assertIs(game.toggle_mark(3, 3), Mark.NONE)
        self.assertFalse(game.board.cell(3, 3).is_open)

    def test_new_game_resets_state(self):
        game = make_game([(0, 0)])
        game.reveal(0, 0)
        game.new_game(BEGINNER)
        self.assertIs(game.state, GameState.READY)
        self.assertIsNone(game.exploded)
        self.assertEqual(game.board.rows, 9)
        self.assertEqual(game.elapsed, 0)


class MarkTest(unittest.TestCase):
    """Флажки и знаки вопроса."""

    def test_mark_cycle_with_question_marks(self):
        game = make_game([(0, 0)])
        self.assertIs(game.toggle_mark(0, 0), Mark.FLAG)
        self.assertIs(game.toggle_mark(0, 0), Mark.QUESTION)
        self.assertIs(game.toggle_mark(0, 0), Mark.NONE)

    def test_mark_cycle_without_question_marks(self):
        game = make_game([(0, 0)], question_marks=False)
        self.assertIs(game.toggle_mark(0, 0), Mark.FLAG)
        self.assertIs(game.toggle_mark(0, 0), Mark.NONE)

    def test_disabling_question_marks_clears_them(self):
        game = make_game([(0, 0)])
        game.toggle_mark(0, 0)
        game.toggle_mark(0, 0)
        cleared = game.set_question_marks(False)
        self.assertEqual(cleared, [game.board.cell(0, 0)])
        self.assertIs(game.board.cell(0, 0).mark, Mark.NONE)

    def test_flag_protects_from_reveal(self):
        game = make_game([(0, 0)])
        game.toggle_mark(0, 0)
        self.assertEqual(game.reveal(0, 0), [])
        self.assertIs(game.state, GameState.PLAYING)

    def test_mines_left_counts_flags(self):
        game = make_game([(0, 0), (3, 3)])
        game.toggle_mark(0, 1)
        game.toggle_mark(0, 2)
        game.toggle_mark(0, 3)
        self.assertEqual(game.mines_left, -1)

    def test_cannot_mark_open_cell(self):
        game = make_game([(0, 0)])
        game.reveal(0, 1)
        self.assertIs(game.toggle_mark(0, 1), Mark.NONE)


class ChordTest(unittest.TestCase):
    """Открытие соседей цифры («аккорд»)."""

    def setUp(self):
        # Мины в (0, 0) и (0, 3); клетка (1, 1) — цифра 1.
        self.game = make_game([(0, 0), (0, 3)])
        self.game.reveal(1, 1)

    def test_chord_with_correct_flag(self):
        self.game.toggle_mark(0, 0)
        opened = self.game.chord(1, 1)
        self.assertTrue(opened)
        self.assertTrue(self.game.board.cell(0, 1).is_open)
        self.assertTrue(self.game.board.cell(2, 2).is_open)
        # Пустые клетки снизу открыли всё поле — это победа.
        self.assertIs(self.game.state, GameState.WON)

    def test_chord_ignored_without_enough_flags(self):
        self.assertEqual(self.game.chord(1, 1), [])

    def test_chord_with_wrong_flag_explodes(self):
        self.game.toggle_mark(1, 0)  # флажок не там, где мина
        self.game.chord(1, 1)
        self.assertIs(self.game.state, GameState.LOST)
        self.assertIs(self.game.exploded, self.game.board.cell(0, 0))

    def test_chord_on_closed_cell_does_nothing(self):
        self.assertEqual(self.game.chord(3, 3), [])


class TimerTest(unittest.TestCase):
    """Таймер партии."""

    def test_timer_starts_on_first_move_and_stops_on_finish(self):
        clock = FakeClock()
        game = MinesweeperGame(BEGINNER, rng=random.Random(3), clock=clock)
        clock.now += 50
        self.assertEqual(game.elapsed, 0)  # до первого хода время стоит
        game.reveal(4, 4)
        clock.now += 7.6
        self.assertEqual(game.elapsed, 7)
        mine = next(cell for cell in game.board if cell.is_mine)
        game.reveal(mine.row, mine.col)
        clock.now += 30
        self.assertEqual(game.elapsed, 7)

    def test_timer_is_capped(self):
        clock = FakeClock()
        game = MinesweeperGame(BEGINNER, clock=clock)
        game.reveal(0, 0)
        clock.now += 5000
        self.assertEqual(game.elapsed, 999)


if __name__ == "__main__":
    unittest.main()
