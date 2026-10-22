"""Тесты таблицы рекордов и уровней сложности."""

import json
import tempfile
import unittest
from pathlib import Path

from src.models.difficulty import EXPERT, MAX_COLS, custom, max_mines
from src.models.records import RecordsTable
from src.renderers.hud_renderer import SEGMENTS_OF, format_counter


class RecordsTableTest(unittest.TestCase):
    """Сохранение лучших результатов."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "records.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_first_result_is_record(self):
        table = RecordsTable(self.path)
        self.assertIsNone(table.best("beginner"))
        self.assertTrue(table.submit("beginner", 42))
        self.assertEqual(table.best("beginner")["time"], 42)

    def test_only_better_time_replaces_record(self):
        table = RecordsTable(self.path)
        table.submit("beginner", 42)
        self.assertFalse(table.submit("beginner", 50))
        self.assertFalse(table.submit("beginner", 42))
        self.assertTrue(table.submit("beginner", 30))
        self.assertEqual(table.best("beginner")["time"], 30)

    def test_records_are_saved_to_file(self):
        RecordsTable(self.path).submit("expert", 300)
        self.assertEqual(RecordsTable(self.path).best("expert")["time"], 300)

    def test_corrupted_file_is_ignored(self):
        self.path.write_text("{ это не JSON", encoding="utf-8")
        self.assertIsNone(RecordsTable(self.path).best("beginner"))
        self.path.write_text(json.dumps({"beginner": {"time": "x"}}),
                             encoding="utf-8")
        self.assertIsNone(RecordsTable(self.path).best("beginner"))

    def test_clear(self):
        table = RecordsTable(self.path)
        table.submit("beginner", 10)
        table.clear()
        self.assertIsNone(RecordsTable(self.path).best("beginner"))


class DifficultyTest(unittest.TestCase):
    """Уровни сложности."""

    def test_expert_preset(self):
        self.assertEqual((EXPERT.rows, EXPERT.cols, EXPERT.mines),
                         (16, 30, 99))

    def test_custom_level_is_clamped(self):
        level = custom(2, 100, 10_000)
        self.assertEqual(level.rows, 5)
        self.assertEqual(level.cols, MAX_COLS)
        self.assertEqual(level.mines, max_mines(5, MAX_COLS))
        self.assertEqual(custom(10, 10, 0).mines, 1)


class CounterFormatTest(unittest.TestCase):
    """Формат чисел для семисегментного индикатора."""

    def test_format(self):
        self.assertEqual(format_counter(7), "007")
        self.assertEqual(format_counter(99), "099")
        self.assertEqual(format_counter(-5), "-05")
        self.assertEqual(format_counter(5000), "999")
        self.assertEqual(format_counter(-500), "-99")

    def test_all_symbols_have_segments(self):
        for value in range(-99, 1000):
            for char in format_counter(value):
                self.assertIn(char, SEGMENTS_OF)


if __name__ == "__main__":
    unittest.main()
