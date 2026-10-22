"""Константы оформления и настройки игры «Сапёр»."""

from pathlib import Path

WINDOW_TITLE = "Сапёр"

# Геометрия (пиксели).
CELL_SIZE = 28          # сторона клетки
BEVEL = 3               # толщина «объёмной» рамки закрытой клетки
HUD_HEIGHT = 52         # высота верхней панели со счётчиками
FRAME_PADDING = 8       # отступ вокруг поля и панели

# Классическая серая палитра.
COLOR_FACE = "#c0c0c0"
COLOR_LIGHT = "#ffffff"
COLOR_SHADOW = "#808080"
COLOR_OPEN = "#bdbdbd"
COLOR_GRID = "#7b7b7b"
COLOR_EXPLODED = "#ff2b1c"
COLOR_MINE = "#111111"
COLOR_FLAG = "#e0201b"
COLOR_CROSS = "#e0201b"

# Цвета цифр — как в классической версии игры.
NUMBER_COLORS = {
    1: "#0000ff", 2: "#007b00", 3: "#ff0000", 4: "#00007b",
    5: "#7b0000", 6: "#007b7b", 7: "#000000", 8: "#7b7b7b",
}
NUMBER_FONT = ("Helvetica", -18, "bold")   # отрицательный размер — пиксели

# Семисегментные индикаторы.
DISPLAY_BG = "#000000"
SEGMENT_ON = "#ff1a1a"
SEGMENT_OFF = "#3d0505"

# Смайлик.
FACE_YELLOW = "#ffeb3b"

# Анимация.
REVEAL_STEP_MS = 22        # задержка между «кольцами» волны открытия
MAX_REVEAL_TIME_MS = 450   # вся волна не дольше этого времени
EXPLOSION_STEP_MS = 40     # интервал между взрывами мин при проигрыше
MAX_EXPLOSION_TIME_MS = 1600
TIMER_TICK_MS = 200        # как часто обновлять таймер
WIN_MESSAGE_DELAY_MS = 500

# Файл с рекордами хранится в домашней папке пользователя.
RECORDS_FILE = Path.home() / ".ppp_minesweeper_records.json"
