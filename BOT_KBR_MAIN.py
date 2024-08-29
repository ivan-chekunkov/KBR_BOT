import asyncio
import os
import shutil
import sqlite3
import time

from pathlib import Path
from re import search

from loguru import logger

from settings import load as load_settings

version = "1.7"

SQL_CHECK_DB = """
    SELECT
        count(*)
    FROM
        sqlite_master
    WHERE
        TYPE = 'table'
        AND name = 'LOGS'
"""

SQL_DROP_DB = """DROP TABLE IF EXISTS LOGS"""

SQL_CREATE_DB = """
    CREATE TABLE LOGS (
        id INTEGER PRIMARY KEY,
        name VARCHAR(100),
        cheked int
    )
"""

SQL_INSERT_LOGS = """
    INSERT INTO
        LOGS (name, cheked)
    VALUES
        (?, ?)
"""

logger.add(
    "Logfile.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="10 MB",
    compression="zip",
)


def net_use_drive():
    try:
        if Path("{}:\\".format(SETTINGS["drive"])).exists():
            return None
    except Exception as error:
        logger.error(error)
    while True:
        try:
            os.system(
                "cmd /c net use {}: {}".format(
                    SETTINGS["drive"], SETTINGS["connect_path"]
                )
            )
            if Path("{}:\\".format(SETTINGS["drive"])).exists():
                logger.info(
                    "Диск {} примонтирован успешно".format(SETTINGS["drive"])
                )
                break
            else:
                try:
                    time.sleep(5)
                    os.system(
                        'cmd /c "net use {}: /del"'.format(SETTINGS["drive"])
                    )
                    time.sleep(5)
                except Exception as error:
                    logger.error(error)
        except Exception as error:
            logger.error(error)
            try:
                time.sleep(5)
                os.system(
                    'cmd /c "net use {}: /del"'.format(SETTINGS["drive"])
                )
                time.sleep(5)
            except Exception as error:
                logger.error(error)


def check_db_and_get_con(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    with con:
        data = con.execute(SQL_CHECK_DB)
        for row in data:
            if row[0] == 0:
                logger.info("База была пустой")
                con.execute(SQL_DROP_DB)
                con.execute(SQL_CREATE_DB)
    return con


def start() -> None:
    net_use_drive()
    for schema in SETTINGS["schemas"]:
        file_list = []
        for path_file in Path(schema["base"]).iterdir():
            if schema.get("regex") and schema.get("regex_path"):
                if search(schema["regex"], path_file.name):
                    kwit_path = schema["regex_path"]
                    new_path = Path(kwit_path).joinpath(path_file.name)
                    shutil.copy(path_file, new_path)
                    path_file.unlink()
                    logger.info(
                        "Файл {} перемещен в {}".format(path_file, new_path)
                    )
            if path_file.is_file():
                for path_arh in schema["arh"]:
                    new_path = Path(path_arh).joinpath(path_file.name)
                    shutil.copy(path_file, new_path)
                    logger.info(
                        "Файл {} скопирован в {}".format(path_file, new_path)
                    )
                new_path = Path(schema["move"]).joinpath(path_file.name)
                shutil.copy(path_file, new_path)
                path_file.unlink()
                file_list.append(path_file.name)
                logger.info(
                    "Файл {} перемещен в {}".format(path_file, new_path)
                )
        if file_list and schema.get("log"):
            path_log = schema["log"]
            con = check_db_and_get_con(path_log)
            data = list(map(lambda x: (x, 0), [x for x in file_list]))
            with con:
                try:
                    con.executemany(SQL_INSERT_LOGS, data)
                    logger.debug("Записи добавлены в базу")
                except Exception as error:
                    logger.error(
                        "Ошибка при добавлении в базу: {}".format(error)
                    )


def _del_drive() -> int:
    return os.system(
        'cmd /c "net use {}: /del /y{}"'.format(
            SETTINGS["drive"], SETTINGS["silence_mode"]
        )
    )


async def monitoring() -> None:
    while True:
        start()
        await asyncio.sleep(SETTINGS["tics"])


def _exit():
    logger.debug("Завершение работы программы!")
    res = _del_drive()
    if res == 2:
        logger.error("Не удалось удалить диск {}".format(SETTINGS["drive"]))


if __name__ == "__main__":
    logger.debug("Запуск скрипта версии: {}".format(version))
    try:
        SETTINGS = load_settings(file_name="kbr_settings.json", log=False)
    except Exception as error:
        logger.error("Ошибка при загрузке kbr_settings.json: {}".format(error))
    if SETTINGS.get("silence_mode"):
        SETTINGS["silence_mode"] = ">nul 2>&1"
        logger.debug("Включен режим тишины для комманд")
    else:
        SETTINGS["silence_mode"] = ""
        logger.debug("Настройка silence_mode либо не указана либо равна false")
        logger.debug("Выключен режим тишины для комманд")
    res = _del_drive()
    if res == 2:
        logger.error("Не удалось удалить диск {}".format(SETTINGS["drive"]))
    logger.debug("Запускаю мониторинг")
    while True:
        try:
            asyncio.run(monitoring())
            input()
        except KeyboardInterrupt:
            _exit()
        except Exception as error:
            logger.error(error)
            time.sleep(10)
