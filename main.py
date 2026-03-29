"""应用入口"""

import sys
from PySide6.QtWidgets import QApplication

from control_window import ControlWindow


def main():
    app = QApplication(sys.argv)
    window = ControlWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
