"""Qt Stylesheet 主题定义 — 5 套完整配色方案。"""

# ---- 浅色主题 (默认) ----

THEME_LIGHT = """
QMainWindow { background-color: #f5f5f5; }
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f9f9f9;
    gridline-color: #e0e0e0;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
    border: 1px solid #dddddd;
}
QTableWidget::item { padding: 4px; }
QListWidget {
    background-color: #f0f0f0;
    border: none;
    outline: none;
}
QListWidget::item { padding: 8px 12px; border-radius: 4px; }
QListWidget::item:selected { background-color: #4a90d9; color: #ffffff; }
QListWidget::item:hover:!selected { background-color: #e0e0e0; }
QPushButton {
    background-color: #e1e1e1; border: 1px solid #c0c0c0;
    border-radius: 4px; padding: 6px 14px; color: #333333;
}
QPushButton:hover { background-color: #d0d0d0; }
QPushButton:pressed { background-color: #c0c0c0; }
QLineEdit {
    border: 1px solid #c0c0c0; border-radius: 4px;
    padding: 4px 8px; background-color: #ffffff; color: #333333;
}
QLineEdit:focus { border-color: #0078d4; }
QStatusBar { background-color: #f0f0f0; border-top: 1px solid #dddddd; color: #333333; }
QSplitter::handle { background-color: #d0d0d0; width: 2px; }
QLabel { color: #333333; }
QHeaderView::section {
    background-color: #f0f0f0; padding: 4px 8px; border: none;
    border-right: 1px solid #d0d0d0; border-bottom: 1px solid #d0d0d0; color: #333333;
}
QComboBox {
    border: 1px solid #c0c0c0; border-radius: 4px;
    padding: 4px 8px; background-color: #ffffff; color: #333333;
}
QTabWidget::pane { border: 1px solid #d0d0d0; background-color: #ffffff; }
QTabBar::tab {
    background-color: #e8e8e8; padding: 8px 16px;
    border: 1px solid #d0d0d0; border-bottom: none; color: #333333;
}
QTabBar::tab:selected { background-color: #ffffff; }
QTextEdit {
    border: 1px solid #c0c0c0; border-radius: 4px;
    background-color: #ffffff; color: #333333;
}
QFrame[statsLabel="true"] { background-color: #f5f5f5; border-top: 1px solid #dddddd; }
QMessageBox { background-color: #f5f5f5; }
QDateEdit {
    border: 1px solid #c0c0c0; border-radius: 4px;
    padding: 4px 8px; background-color: #ffffff;
}
QScrollBar:vertical { background-color: #f0f0f0; width: 10px; }
QScrollBar::handle:vertical { background-color: #c0c0c0; border-radius: 5px; min-height: 20px; }
QScrollBar:horizontal { background-color: #f0f0f0; height: 10px; }
QScrollBar::handle:horizontal { background-color: #c0c0c0; border-radius: 5px; min-width: 20px; }
QSpinBox {
    border: 1px solid #c0c0c0; border-radius: 4px;
    padding: 4px 8px; background-color: #ffffff;
}
"""

# ---- 深色主题 ----

THEME_DARK = """
QMainWindow { background-color: #1e1e1e; }
QTableWidget {
    background-color: #252526; alternate-background-color: #2d2d2d;
    gridline-color: #3e3e3e; selection-background-color: #264f78;
    selection-color: #ffffff; border: 1px solid #3e3e3e; color: #d4d4d4;
}
QTableWidget::item { padding: 4px; }
QListWidget {
    background-color: #252526; border: none; outline: none; color: #d4d4d4;
}
QListWidget::item { padding: 8px 12px; border-radius: 4px; }
QListWidget::item:selected { background-color: #264f78; color: #ffffff; }
QListWidget::item:hover:!selected { background-color: #3c3c3c; }
QPushButton {
    background-color: #3c3c3c; border: 1px solid #555555;
    border-radius: 4px; padding: 6px 14px; color: #d4d4d4;
}
QPushButton:hover { background-color: #4a4a4a; }
QPushButton:pressed { background-color: #555555; }
QLineEdit {
    border: 1px solid #555555; border-radius: 4px;
    padding: 4px 8px; background-color: #3c3c3c; color: #d4d4d4;
}
QLineEdit:focus { border-color: #0078d4; }
QStatusBar { background-color: #252526; border-top: 1px solid #3e3e3e; color: #d4d4d4; }
QSplitter::handle { background-color: #3e3e3e; width: 2px; }
QLabel { color: #d4d4d4; }
QHeaderView::section {
    background-color: #2d2d2d; padding: 4px 8px; border: none;
    border-right: 1px solid #3e3e3e; border-bottom: 1px solid #3e3e3e; color: #d4d4d4;
}
QComboBox {
    border: 1px solid #555555; border-radius: 4px;
    padding: 4px 8px; background-color: #3c3c3c; color: #d4d4d4;
}
QTabWidget::pane { border: 1px solid #3e3e3e; background-color: #252526; }
QTabBar::tab {
    background-color: #2d2d2d; padding: 8px 16px;
    border: 1px solid #3e3e3e; border-bottom: none; color: #d4d4d4;
}
QTabBar::tab:selected { background-color: #252526; }
QTextEdit {
    border: 1px solid #555555; border-radius: 4px;
    background-color: #252526; color: #d4d4d4;
}
QFrame[statsLabel="true"] { background-color: #2d2d2d; border-top: 1px solid #3e3e3e; }
QMessageBox { background-color: #2d2d2d; color: #d4d4d4; }
QDateEdit {
    border: 1px solid #555555; border-radius: 4px;
    padding: 4px 8px; background-color: #3c3c3c; color: #d4d4d4;
}
QScrollBar:vertical { background-color: #2d2d2d; width: 10px; }
QScrollBar::handle:vertical { background-color: #555555; border-radius: 5px; min-height: 20px; }
QScrollBar:horizontal { background-color: #2d2d2d; height: 10px; }
QScrollBar::handle:horizontal { background-color: #555555; border-radius: 5px; min-width: 20px; }
QSpinBox {
    border: 1px solid #555555; border-radius: 4px;
    padding: 4px 8px; background-color: #3c3c3c; color: #d4d4d4;
}
"""

# ---- Solarized Light ----

THEME_SOLARIZED_LIGHT = """
QMainWindow { background-color: #fdf6e3; }
QTableWidget {
    background-color: #fdf6e3; alternate-background-color: #eee8d5;
    gridline-color: #93a1a1; selection-background-color: #268bd2;
    selection-color: #ffffff; border: 1px solid #93a1a1; color: #657b83;
}
QTableWidget::item { padding: 4px; }
QListWidget {
    background-color: #eee8d5; border: none; outline: none; color: #657b83;
}
QListWidget::item { padding: 8px 12px; border-radius: 4px; }
QListWidget::item:selected { background-color: #268bd2; color: #ffffff; }
QListWidget::item:hover:!selected { background-color: #e0dcc8; }
QPushButton {
    background-color: #93a1a1; border: 1px solid #839496;
    border-radius: 4px; padding: 6px 14px; color: #fdf6e3;
}
QPushButton:hover { background-color: #839496; }
QPushButton:pressed { background-color: #657b83; }
QLineEdit {
    border: 1px solid #93a1a1; border-radius: 4px;
    padding: 4px 8px; background-color: #fdf6e3; color: #657b83;
}
QLineEdit:focus { border-color: #268bd2; }
QStatusBar { background-color: #eee8d5; border-top: 1px solid #93a1a1; color: #657b83; }
QSplitter::handle { background-color: #93a1a1; width: 2px; }
QLabel { color: #657b83; }
QHeaderView::section {
    background-color: #eee8d5; padding: 4px 8px; border: none;
    border-right: 1px solid #93a1a1; border-bottom: 1px solid #93a1a1; color: #657b83;
}
QComboBox {
    border: 1px solid #93a1a1; border-radius: 4px;
    padding: 4px 8px; background-color: #fdf6e3; color: #657b83;
}
QTabWidget::pane { border: 1px solid #93a1a1; background-color: #fdf6e3; }
QTabBar::tab {
    background-color: #eee8d5; padding: 8px 16px;
    border: 1px solid #93a1a1; border-bottom: none; color: #657b83;
}
QTabBar::tab:selected { background-color: #fdf6e3; }
QTextEdit {
    border: 1px solid #93a1a1; border-radius: 4px;
    background-color: #fdf6e3; color: #657b83;
}
QFrame[statsLabel="true"] { background-color: #eee8d5; border-top: 1px solid #93a1a1; }
QScrollBar:vertical { background-color: #eee8d5; width: 10px; }
QScrollBar::handle:vertical { background-color: #93a1a1; border-radius: 5px; min-height: 20px; }
QScrollBar:horizontal { background-color: #eee8d5; height: 10px; }
QScrollBar::handle:horizontal { background-color: #93a1a1; border-radius: 5px; min-width: 20px; }
QSpinBox {
    border: 1px solid #93a1a1; border-radius: 4px;
    padding: 4px 8px; background-color: #fdf6e3; color: #657b83;
}
"""

# ---- Solarized Dark ----

THEME_SOLARIZED_DARK = """
QMainWindow { background-color: #002b36; }
QTableWidget {
    background-color: #002b36; alternate-background-color: #073642;
    gridline-color: #586e75; selection-background-color: #2aa198;
    selection-color: #ffffff; border: 1px solid #586e75; color: #839496;
}
QTableWidget::item { padding: 4px; }
QListWidget {
    background-color: #073642; border: none; outline: none; color: #839496;
}
QListWidget::item { padding: 8px 12px; border-radius: 4px; }
QListWidget::item:selected { background-color: #2aa198; color: #ffffff; }
QListWidget::item:hover:!selected { background-color: #0a4d5c; }
QPushButton {
    background-color: #586e75; border: 1px solid #657b83;
    border-radius: 4px; padding: 6px 14px; color: #eee8d5;
}
QPushButton:hover { background-color: #657b83; }
QPushButton:pressed { background-color: #839496; }
QLineEdit {
    border: 1px solid #586e75; border-radius: 4px;
    padding: 4px 8px; background-color: #073642; color: #839496;
}
QLineEdit:focus { border-color: #2aa198; }
QStatusBar { background-color: #073642; border-top: 1px solid #586e75; color: #839496; }
QSplitter::handle { background-color: #586e75; width: 2px; }
QLabel { color: #839496; }
QHeaderView::section {
    background-color: #073642; padding: 4px 8px; border: none;
    border-right: 1px solid #586e75; border-bottom: 1px solid #586e75; color: #839496;
}
QComboBox {
    border: 1px solid #586e75; border-radius: 4px;
    padding: 4px 8px; background-color: #073642; color: #839496;
}
QTabWidget::pane { border: 1px solid #586e75; background-color: #002b36; }
QTabBar::tab {
    background-color: #073642; padding: 8px 16px;
    border: 1px solid #586e75; border-bottom: none; color: #839496;
}
QTabBar::tab:selected { background-color: #002b36; }
QTextEdit {
    border: 1px solid #586e75; border-radius: 4px;
    background-color: #073642; color: #839496;
}
QFrame[statsLabel="true"] { background-color: #073642; border-top: 1px solid #586e75; }
QScrollBar:vertical { background-color: #073642; width: 10px; }
QScrollBar::handle:vertical { background-color: #586e75; border-radius: 5px; min-height: 20px; }
QScrollBar:horizontal { background-color: #073642; height: 10px; }
QScrollBar::handle:horizontal { background-color: #586e75; border-radius: 5px; min-width: 20px; }
QSpinBox {
    border: 1px solid #586e75; border-radius: 4px;
    padding: 4px 8px; background-color: #073642; color: #839496;
}
"""

# ---- Nord ----

THEME_NORD = """
QMainWindow { background-color: #2e3440; }
QTableWidget {
    background-color: #2e3440; alternate-background-color: #3b4252;
    gridline-color: #4c566a; selection-background-color: #5e81ac;
    selection-color: #eceff4; border: 1px solid #4c566a; color: #d8dee9;
}
QTableWidget::item { padding: 4px; }
QListWidget {
    background-color: #3b4252; border: none; outline: none; color: #d8dee9;
}
QListWidget::item { padding: 8px 12px; border-radius: 4px; }
QListWidget::item:selected { background-color: #5e81ac; color: #eceff4; }
QListWidget::item:hover:!selected { background-color: #434c5e; }
QPushButton {
    background-color: #4c566a; border: 1px solid #5e81ac;
    border-radius: 4px; padding: 6px 14px; color: #eceff4;
}
QPushButton:hover { background-color: #5e81ac; }
QPushButton:pressed { background-color: #81a1c1; }
QLineEdit {
    border: 1px solid #4c566a; border-radius: 4px;
    padding: 4px 8px; background-color: #3b4252; color: #d8dee9;
}
QLineEdit:focus { border-color: #88c0d0; }
QStatusBar { background-color: #3b4252; border-top: 1px solid #4c566a; color: #d8dee9; }
QSplitter::handle { background-color: #4c566a; width: 2px; }
QLabel { color: #d8dee9; }
QHeaderView::section {
    background-color: #3b4252; padding: 4px 8px; border: none;
    border-right: 1px solid #4c566a; border-bottom: 1px solid #4c566a; color: #d8dee9;
}
QComboBox {
    border: 1px solid #4c566a; border-radius: 4px;
    padding: 4px 8px; background-color: #3b4252; color: #d8dee9;
}
QTabWidget::pane { border: 1px solid #4c566a; background-color: #2e3440; }
QTabBar::tab {
    background-color: #3b4252; padding: 8px 16px;
    border: 1px solid #4c566a; border-bottom: none; color: #d8dee9;
}
QTabBar::tab:selected { background-color: #2e3440; }
QTextEdit {
    border: 1px solid #4c566a; border-radius: 4px;
    background-color: #3b4252; color: #d8dee9;
}
QFrame[statsLabel="true"] { background-color: #3b4252; border-top: 1px solid #4c566a; }
QScrollBar:vertical { background-color: #3b4252; width: 10px; }
QScrollBar::handle:vertical { background-color: #4c566a; border-radius: 5px; min-height: 20px; }
QScrollBar:horizontal { background-color: #3b4252; height: 10px; }
QScrollBar::handle:horizontal { background-color: #4c566a; border-radius: 5px; min-width: 20px; }
QSpinBox {
    border: 1px solid #4c566a; border-radius: 4px;
    padding: 4px 8px; background-color: #3b4252; color: #d8dee9;
}
"""

# ---- 主题字典 ----

THEMES = {
    "light": THEME_LIGHT,
    "dark": THEME_DARK,
    "solarized_light": THEME_SOLARIZED_LIGHT,
    "solarized_dark": THEME_SOLARIZED_DARK,
    "nord": THEME_NORD,
}

THEME_NAMES = ["light", "dark", "solarized_light", "solarized_dark", "nord"]

THEME_DISPLAY = {
    "light": "浅色",
    "dark": "深色",
    "solarized_light": "Solarized 浅色",
    "solarized_dark": "Solarized 深色",
    "nord": "Nord",
}
