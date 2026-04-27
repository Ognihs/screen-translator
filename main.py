"""应用入口"""

import logging
import sys
from PySide6.QtWidgets import QApplication

from control_window import ControlWindow


def _configure_logging():
    """配置日志记录"""
    import os

    # 从环境变量读取日志级别，默认 WARNING
    log_level_str = os.getenv("LOG_LEVEL", "WARNING")
    log_level = getattr(logging, log_level_str.upper(), logging.WARNING)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    _configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("应用启动")
    try:
        app = QApplication(sys.argv)
        window = ControlWindow()
        window.show()
        logger.info("应用窗口已显示")
        exit_code = app.exec()
        logger.info(f"应用退出，退出码: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"应用启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
