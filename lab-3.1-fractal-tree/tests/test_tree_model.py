"""Тесты математической модели фрактального дерева."""

import math
import unittest

from src.models.tree_model import (FractalTree, Segment, bounding_box,
                                   grow_stage)


class FractalTreeTest(unittest.TestCase):
    """Проверка рекурсивного построения ветвей."""

    def test_segment_count_is_power_of_two_minus_one(self):
        for depth in range(1, 12):
            tree = FractalTree(30, 0.67, depth)
            self.assertEqual(len(tree.build()), 2 ** depth - 1)
            self.assertEqual(tree.segment_count, 2 ** depth - 1)

    def test_trunk_is_vertical_unit_segment(self):
        trunk = FractalTree(45, 0.5, 3).build()[0]
        self.assertEqual(trunk.level, 0)
        self.assertAlmostEqual(trunk.x1, 0.0)
        self.assertAlmostEqual(trunk.y1, 0.0)
        self.assertAlmostEqual(trunk.x2, 0.0)
        self.assertAlmostEqual(trunk.y2, 1.0)

    def test_children_are_shorter_by_ratio(self):
        ratio = 0.6
        for segment in FractalTree(25, ratio, 6).build():
            self.assertAlmostEqual(segment.length, ratio ** segment.level)

    def test_children_turn_by_angle_in_both_directions(self):
        trunk, left, *_ = FractalTree(40, 0.7, 2).build()
        right = FractalTree(40, 0.7, 2).build()[2]
        self.assertAlmostEqual(left.heading, 90 + 40)
        self.assertAlmostEqual(right.heading, 90 - 40)
        # Обе ветви начинаются из конца ствола.
        self.assertAlmostEqual(left.x1, trunk.x2)
        self.assertAlmostEqual(right.y1, trunk.y2)

    def test_zero_angle_gives_straight_line(self):
        segments = FractalTree(0, 0.5, 5).build()
        for segment in segments:
            self.assertAlmostEqual(segment.x2, 0.0)
        top = max(s.y2 for s in segments)
        # Сумма геометрической прогрессии 1 + 1/2 + 1/4 + 1/8 + 1/16.
        self.assertAlmostEqual(top, 2 - 0.5 ** 4)

    def test_tree_is_symmetric(self):
        segments = FractalTree(33, 0.67, 8).build()
        min_x, _, max_x, _ = bounding_box(segments)
        self.assertAlmostEqual(min_x, -max_x)
        self.assertAlmostEqual(sum(s.x2 for s in segments), 0.0, places=9)

    def test_invalid_parameters_raise(self):
        with self.assertRaises(ValueError):
            FractalTree(-1, 0.5, 3)
        with self.assertRaises(ValueError):
            FractalTree(181, 0.5, 3)
        with self.assertRaises(ValueError):
            FractalTree(30, 1.0, 3)
        with self.assertRaises(ValueError):
            FractalTree(30, 0.0, 3)
        with self.assertRaises(ValueError):
            FractalTree(30, 0.5, 0)

    def test_parameters_can_be_changed(self):
        tree = FractalTree(30, 0.67, 3)
        tree.angle = 90
        tree.depth = 2
        left = tree.build()[1]
        self.assertAlmostEqual(left.heading, 180)
        self.assertEqual(len(tree.build()), 3)


class GrowStageTest(unittest.TestCase):
    """Проверка частичного дерева для анимации роста."""

    def setUp(self):
        self.segments = FractalTree(30, 0.5, 4).build()

    def test_nothing_before_growth(self):
        self.assertEqual(grow_stage(self.segments, 0), [])

    def test_trunk_grows_first(self):
        stage = grow_stage(self.segments, 0.5)
        self.assertEqual(len(stage), 1)
        self.assertAlmostEqual(stage[0].length, 0.5)

    def test_next_level_is_partial(self):
        stage = grow_stage(self.segments, 1.25)
        self.assertEqual(len(stage), 3)
        self.assertAlmostEqual(stage[0].length, 1.0)
        self.assertAlmostEqual(stage[1].length, 0.5 * 0.25)

    def test_full_growth_returns_all_segments(self):
        self.assertEqual(grow_stage(self.segments, 4), self.segments)
        self.assertEqual(grow_stage(self.segments, 100), self.segments)


class GeometryHelpersTest(unittest.TestCase):
    """Проверка вспомогательных функций."""

    def test_partial_segment_keeps_start(self):
        part = Segment(1, 1, 3, 5, 2).partial(0.5)
        self.assertEqual((part.x1, part.y1, part.x2, part.y2), (1, 1, 2, 3))
        self.assertEqual(part.level, 2)

    def test_heading(self):
        self.assertAlmostEqual(Segment(0, 0, 1, 1, 0).heading, 45)
        self.assertAlmostEqual(Segment(0, 0, 0, 1, 0).length, 1)
        self.assertAlmostEqual(Segment(0, 0, -1, 0, 0).heading, 180)

    def test_bounding_box(self):
        segments = [Segment(0, 0, 2, 1, 0), Segment(-1, 3, 0, -2, 1)]
        self.assertEqual(bounding_box(segments), (-1, -2, 2, 3))
        self.assertEqual(bounding_box([]), (0, 0, 0, 0))

    def test_bounding_box_of_wide_tree(self):
        segments = FractalTree(90, 0.5, 2).build()
        min_x, min_y, max_x, max_y = bounding_box(segments)
        self.assertAlmostEqual(max_x, 0.5)
        self.assertAlmostEqual(min_x, -0.5)
        self.assertAlmostEqual(max_y, 1.0)
        self.assertTrue(math.isclose(min_y, 0.0, abs_tol=1e-12))


if __name__ == "__main__":
    unittest.main()
