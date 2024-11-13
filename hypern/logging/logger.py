# -*- coding: utf-8 -*-
import logging
from typing import Optional, Literal
from copy import copy
import click
import sys

TRACE_LOG_LEVEL = 5


class ColourizedFormatter(logging.Formatter):
    level_name_colors = {
        TRACE_LOG_LEVEL: lambda level_name: click.style(str(level_name), fg="blue"),
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(str(level_name), fg="bright_red"),
    }

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        style: Literal["%", "{", "$"] = "%",
        use_colors: Optional[bool] = None,
    ):
        if use_colors in (True, False):
            self.use_colors = use_colors
        else:
            self.use_colors = sys.stdout.isatty()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    def color_level_name(self, level_name: str, level_no: int) -> str:
        def default(level_name: str) -> str:
            return str(level_name)

        func = self.level_name_colors.get(level_no, default)
        return func(level_name)

    def should_use_colors(self) -> bool:
        return True

    def formatMessage(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        levelname = recordcopy.levelname
        process = recordcopy.process
        separator = " " * (8 - len(recordcopy.levelname))
        if self.use_colors:
            levelname = self.color_level_name(levelname, recordcopy.levelno)
            if "color_message" in recordcopy.__dict__:
                recordcopy.msg = recordcopy.__dict__["color_message"]
                recordcopy.__dict__["message"] = recordcopy.getMessage()
        recordcopy.__dict__["levelprefix"] = levelname + ":" + separator
        recordcopy.__dict__["process"] = click.style(str(process), fg="blue")
        return super().formatMessage(recordcopy)


class DefaultFormatter(ColourizedFormatter):
    def should_use_colors(self) -> bool:
        return sys.stderr.isatty()


def create_logger(name) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    formatter = DefaultFormatter(
        fmt="%(levelprefix)s %(asctime)s [%(process)s] [%(filename)s:%(lineno)d] %(message)s",
        use_colors=True,
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def get_loggers_by_prefix(prefix):
    return [name for name in logging.root.manager.loggerDict.keys() if name.startswith(prefix)]


def reset_logger() -> None:
    robyn_loggers = get_loggers_by_prefix("robyn")
    actix_loggers = ["actix_server.builder", "actix_server.worker", "actix_server.server", "actix_server.accept"]

    for name in [*robyn_loggers, *actix_loggers]:
        logger = create_logger(name)
        logger.propagate = False


logger = create_logger("hypern")
