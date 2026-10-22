"""Тесты игрового поля: мины, цифры и открытие областей."""

import random
import unittest

from src.models.board import Board
from src.models.cell import Mark


class BoardTest(unittest.TestCase):
    """Проверка класса Board."""

    def test_neighbors_count(self):
        board = Board(3, 4)
        self.assertEqual(len(list(board.neighbors(0, 0))), 3)
        self.assertEqual(len(list(board.neighbors(0, 1))), 5)
        self.assertEqual(len(list(board.neighbors(1, 1))), 8)

    def test_invalid_size_and_coordinates(self):
        with self.assertRaises(ValueError):
            Board(0, 5)
        with self.assertRaises(IndexError):
            Board(3, 3).cell(3, 0)

    def test_random_mines_count(self):
        board = Board(9, 9)
        board.place_random_mines(10, rng=random.Random(1))
        self.assertEqual(board.mine_count, 10)

    def test_first_click_area_is_safe(self):
        for seed in range(50):
            board = Board(9, 9)
            board.place_random_mines(10, safe=(4, 4),
                                     rng=random.Random(seed))
            self.assertFalse(board.cell(4, 4).is_mine)
            self.assertEqual(board.cell(4, 4).adjacent, 0)
            for neighbor in board.neighbors(4, 4):
                self.assertFalse(neighbor.is_mine)

    def test_dense_board_protects_only_clicked_cell(self):
        board = Board(3, 3)
        board.place_random_mines(8, safe=(1, 1), rng=random.Random(0))
        self.assertFalse(board.cell(1, 1).is_mine)
        self.assertEqual(board.cell(1, 1).adjacent, 8)

    def test_invalid_mine_count(self):
        with self.assertRaises(ValueError):
            Board(3, 3).place_random_mines(9)
        with self.assertRaises(ValueError):
            Board(3, 3).place_random_mines(0)

    def test_adjacent_numbers(self):
        # * 2 0
        # * 2 0
        # 1 1 0
        board = Board(3, 3)
        board.set_mines([(0, 0), (1, 0)])
        numbers = [[board.cell(r, c).adjacent for c in range(3)]
                   for r in range(3)]
        self.assertEqual(numbers[0][1:], [2, 0])
        self.assertEqual(numbers[1][1:], [2, 0])
        self.assertEqual(numbers[2], [1, 1, 0])

    def test_open_number_opens_single_cell(self):
        board = Board(3, 3)
        board.set_mines([(0, 0)])
        opened = board.open_area(1, 1)
        self.assertEqual(len(opened), 1)
        self.assertTrue(board.cell(1, 1).is_open)

    def test_flood_fill_opens_all_safe_cells(self):
        board = Board(5, 5)
        board.set_mines([(0, 0)])
        opened = board.open_area(4, 4)
        self.assertEqual(len(opened), 24)
        self.assertEqual(board.closed_safe_count, 0)
        self.assertFalse(board.cell(0, 0).is_open)
        # Обход в ширину: первой открывается клетка клика.
        self.assertEqual(opened[0].position, (4, 4))

    def test_flood_fill_stops_at_numbers(self):
        # Стена из мин во втором столбце отделяет левую часть поля.
        board = Board(4, 4)
        board.set_mines([(0, 1), (1, 1), (2, 1), (3, 1)])
        board.open_area(0, 3)
        self.assertTrue(board.cell(0, 2).is_open)      # цифра на границе
        self.assertFalse(board.cell(0, 0).is_open)     # за стеной

    def test_flood_fill_skips_flags_and_clears_questions(self):
        board = Board(3, 3)
        board.set_mines([])
        board.cell(0, 0).mark = Mark.FLAG
        board.cell(2, 2).mark = Mark.QUESTION
        opened = board.open_area(1, 1)
        self.assertEqual(len(opened), 8)
        self.assertFalse(board.cell(0, 0).is_open)
        self.assertTrue(board.cell(2, 2).is_open)
        self.assertIs(board.cell(2, 2).mark, Mark.NONE)

    def test_open_flagged_or_opened_cell_does_nothing(self):
        board = Board(3, 3)
        board.set_mines([(0, 0)])
        board.cell(2, 2).mark = Mark.FLAG
        self.assertEqual(board.open_area(2, 2), [])
        board.open_area(1, 1)
        self.assertEqual(board.open_area(1, 1), [])


if __name__ == "__main__":
    unittest.main()
