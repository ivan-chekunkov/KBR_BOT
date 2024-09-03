import sys
import os

from loguru import logger

NAME_MODULE = os.path.basename(__file__).split(".")[0]


def _cls_mode_run(name_module: str, cls_mode: bool = True) -> bool:
    if cls_mode:
        logger.debug(
            "Завершаю работу приложения из модуля = {}".format(name_module)
        )
        sys.exit()
    return False


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
    logger.info(_cls_mode_run(NAME_MODULE))
