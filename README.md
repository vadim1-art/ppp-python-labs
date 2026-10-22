# Лабораторные работы по Python (tkinter)

**Автор:** Готовец Вадим Евгеньевич

**Группа:** ПИ25-1

**Дисциплина:** Практикум по программированию

**Дата сдачи:** 22.10.2026

## Описание репозитория

В репозитории собраны две лабораторные работы, выполненные на Python
с графической библиотекой `tkinter`. У каждой работы своя папка
с собственным `README.md`, точкой входа `main.py`, исходным кодом и тестами.

| Лабораторная | Задание | Папка |
|---|---|---|
| 3.1 «Простая анимация» | Простой фрактал — фрактальное дерево со слайдерами | [`lab-3.1-fractal-tree`](lab-3.1-fractal-tree/README.md) |
| 3.3 «Простые игры» | Сапёр — классическая игра | [`lab-3.3-minesweeper`](lab-3.3-minesweeper/README.md) |

<p align="center">
  <img src="lab-3.1-fractal-tree/screenshots/animation.gif" alt="Фрактальное дерево" height="300">
  &nbsp;
  <img src="lab-3.3-minesweeper/screenshots/gameplay.gif" alt="Сапёр" height="300">
</p>

## Требования к системе

- **Python:** 3.9 или выше
- **Операционная система:** Windows / macOS / Linux
- **Библиотеки:** только стандартная библиотека Python (`tkinter`, `json`,
  `random`, `dataclasses`, `unittest`). На Linux `tkinter` иногда ставится
  отдельно: `sudo apt install python3-tk`.

## Быстрый старт

```bash
git clone https://github.com/vadim1-art/ppp-python-labs.git
cd ppp-python-labs

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Фрактальное дерево
cd lab-3.1-fractal-tree
python main.py

# Сапёр
cd ../lab-3.3-minesweeper
python main.py
```

Виртуальное окружение `venv/` лежит в корне репозитория и общее для обеих
работ (по требованиям к сдаче оно не исключено в `.gitignore`). Окружение
создано на Linux; если на вашей ОС оно не активируется, пересоздайте его:

```bash
python -m venv venv
```

Подробные инструкции, описание функций и управления — в README каждой работы.

## Структура репозитория

```
ppp-python-labs/
├── .gitignore               # исключает __pycache__ и файлы IDE (но не venv/)
├── README.md                # этот файл
├── venv/                    # виртуальное окружение (общее для работ)
├── lab-3.1-fractal-tree/    # ЛР 3.1 — фрактальное дерево
└── lab-3.3-minesweeper/     # ЛР 3.3 — игра «Сапёр»
```

Обе работы устроены одинаково: модель (логика и математика) отделена от
отрисовки и интерфейса. Поэтому модель не зависит от `tkinter` и покрыта
модульными тестами, а `app.py` только связывает модель, отрисовщик и
элементы управления.

## Тесты

```bash
cd lab-3.1-fractal-tree && python -m unittest -v
cd ../lab-3.3-minesweeper && python -m unittest -v
```
