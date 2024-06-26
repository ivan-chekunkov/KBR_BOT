import json
import os
import sys

from loguru import logger


def _cls_mode_run(cls_mode: bool) -> bool:
    if cls_mode:
        logger.debug(
            "Завершаю работу приложения из модуля = {}".format(
                os.path.basename(__file__).split(".")[0]
            )
        )
        sys.exit()
    return False


def _load_json(file_name: str, cls_mode: bool, encoding: str) -> dict | None:
    logger.debug("Загрузка файла настроек: {}!".format(file_name))
    try:
        with open(file=file_name, mode="r", encoding=encoding) as file:
            try:
                result = json.load(file)
                logger.debug("Файл {} загружен - OK!".format(file_name))
            except json.JSONDecodeError as error:
                logger.critical("Некорректный файл настроек!")
                logger.error(error)
                if not _cls_mode_run(cls_mode=cls_mode):
                    return None
            except Exception as error:
                logger.critical("Некорректный файл настроек!")
                logger.error(error)
                if not _cls_mode_run(cls_mode=cls_mode):
                    return None
    except (FileNotFoundError, LookupError) as error:
        logger.critical(
            "Ошибка при открытии файла настроек: {}!".format(file_name)
        )
        logger.error(error)
        if not _cls_mode_run(cls_mode=cls_mode):
            return None
    return result


def load(
    file_name: str = "settings.json",
    cls_mode: bool = True,
    encoding: str = "UTF-8",
) -> dict | None:
    extension = file_name.split(".")[-1]
    if extension == "json":
        result = _load_json(file_name, cls_mode, encoding)
    else:
        logger.critical(
            "Я не умею обрабатывать файлы данного типа: {}".format(extension)
        )
        _cls_mode_run(cls_mode=cls_mode)
        return None
    return result


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
    logger.info(load())
