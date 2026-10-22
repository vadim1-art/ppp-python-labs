"""Точка входа: запуск игры «Сапёр».

Запуск из папки проекта::

    python main.py
"""

from src.app import MinesweeperApp


def main() -> None:
    """Создать окно игры и запустить главный цикл."""
    MinesweeperApp().run()


if __name__ == "__main__":
    main()
