import sys
from loguru import logger


def _cls_mode_run(name_module: str, cls_mode: bool = True) -> bool:
    if cls_mode:
        logger.debug(
            "Завершаю работу приложения из модуля = {}".format(name_module)
        )
        sys.exit()
    return False
