"""Точка входа: запуск приложения «Фрактальное дерево».

Запуск из папки проекта::

    python main.py
"""

from src.app import FractalTreeApp


def main() -> None:
    """Создать окно приложения и запустить главный цикл."""
    FractalTreeApp().run()


if __name__ == "__main__":
    main()
