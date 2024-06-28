import os

from loguru import logger

from tools import _cls_mode_run

NAME_MODULE = os.path.basename(__file__).split(".")[0]


def _create_log():
    logger.add(
        "Logfile_{}.log".format(NAME_MODULE),
        format="{time} {level} {message}",
        level="DEBUG",
        rotation="10 MB",
        compression="zip",
    )


if __name__ == "__main__":
    _create_log()
    logger.info("WAW")
    # settings.load()
    _cls_mode_run(NAME_MODULE)
