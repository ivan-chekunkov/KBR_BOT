import os

from loguru import logger

from settings import _cls_mode_run


def _create_log():
    logger.add(
        "Logfile_{}.log".format(os.path.basename(__file__).split(".")[0]),
        format="{time} {level} {message}",
        level="DEBUG",
        rotation="10 MB",
        compression="zip",
    )


if __name__ == "__main__":
    _create_log()
    logger.info("WAW")
    # settings.load()
    _cls_mode_run(True)
