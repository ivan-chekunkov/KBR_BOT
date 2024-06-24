import asyncio
import os
import shutil
import sqlite3
import time

from datetime import datetime
from pathlib import Path
from typing import Generator

from loguru import logger

from settings import load as load_settings

version = "1.8"


def _adapt_datetime_iso(val):
    return val.isoformat()


def _convert_datetime(val):
    return datetime.fromisoformat(val)


sqlite3.register_adapter(datetime, _adapt_datetime_iso)
sqlite3.register_converter("datetime", _convert_datetime)


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
        cheked int,
        created date
    )
"""

SQL_INSERT_LOGS = """
    INSERT INTO
        LOGS (name, cheked, created)
    VALUES
        (?, ?, ?)
"""

logger.add(
    "Logfile.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="10 MB",
    compression="zip",
)


def _del_drive() -> int:
    return os.system(
        'cmd /c "net use {}: /del /y{}"'.format(
            SETTINGS["drive"], SETTINGS["silence_mode"]
        )
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
                "cmd /c net use {}: {} /y{}".format(
                    SETTINGS["drive"],
                    SETTINGS["connect_path"],
                    SETTINGS["silence_mode"],
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
                    _del_drive()
                    time.sleep(5)
                except Exception as error:
                    logger.error(error)
        except Exception as error:
            logger.error(error)
            try:
                time.sleep(5)
                _del_drive()
                time.sleep(5)
            except Exception as error:
                logger.error(error)


def check_db_and_get_con(path: Path) -> sqlite3.Connection:
    try:
        con = sqlite3.connect(path)
    except Exception as error:
        logger.error("Неудачный коннект к базе: {}".format(error))
    with con:
        data = con.execute(SQL_CHECK_DB)
        for row in data:
            if row[0] == 0:
                logger.info("База была пустой")
                con.executescript(";\n".join((SQL_DROP_DB, SQL_CREATE_DB)))
    return con


def _copy_file(path_file: Path, new_path: Path, log: bool = True) -> None:
    while True:
        try:
            shutil.copy(path_file, new_path)
            break
        except Exception as error:
            logger.error(error)
            time.sleep(5)
            net_use_drive()
    if log:
        logger.info("Файл {} скопирован в {}".format(path_file, new_path))


def _move_file(path_file: Path, new_path: Path) -> None:
    _copy_file(path_file, new_path, log=False)
    while True:
        try:
            path_file.unlink()
            break
        except Exception as error:
            logger.error(error)
            time.sleep(5)
            net_use_drive()
    logger.info("Файл {} перемещен в {}".format(path_file, new_path))


def _iter_dir(path: Path) -> Generator[Path, None, None]:
    while True:
        try:
            logger.debug("Пробую iterdir")
            paths = path.iterdir()
            result = filter(Path.is_file, paths)
            return result
        except OSError:
            logger.error(
                "Ошибка OSError, при нахождении пути к {}".format(path)
            )
        except Exception as error:
            logger.error("Ошибка при нахождении пути к {}".format(path))
            logger.error(error)
        time.sleep(5)
        net_use_drive()


def start() -> None:
    net_use_drive()
    for schema in SETTINGS["schemas"]:
        file_list = []
        for path_file in _iter_dir(Path(schema["base"])):
            for path_arh in schema["arh"]:
                new_path = Path(path_arh).joinpath(path_file.name)
                _copy_file(path_file, new_path)
            new_path = Path(schema["move"]).joinpath(path_file.name)
            _move_file(path_file, new_path)
            file_list.append(path_file.name)
        if file_list and schema.get("log"):
            path_log = schema["log"]
            con = check_db_and_get_con(path_log)
            now_date = datetime.now()
            data = list(
                map(lambda x: (x, 0, now_date), [x for x in file_list])
            )
            with con:
                try:
                    con.executemany(SQL_INSERT_LOGS, data)
                    logger.debug("Записи добавлены в базу")
                except Exception as error:
                    logger.error(
                        "Ошибка при добавлении в базу: {}".format(error)
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
        SETTINGS = load_settings(file_name="spfs_settings.json", log=False)
    except Exception as error:
        logger.error(
            "Ошибка при загрузке spfs_settings.json: {}".format(error)
        )
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
    try:
        asyncio.run(monitoring())
    except KeyboardInterrupt:
        _exit()
