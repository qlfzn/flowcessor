import sys
import logging


class Logger:
    def __init__(self, name: str):
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def info(self, msg: str):
        """
        Logger info method.
        """
        return self.logger.info(msg)

    def warning(self, msg: str, *args):
        """
        Logger warning method.
        """
        return self.logger.warning(msg)
