import asyncio
import os
import shutil
import sqlite3
import time

from datetime import datetime
from pathlib import Path

from loguru import logger

from settings import load as load_settings

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

logger.add('Logfile.log',
           format="{time} {level} {message}",
           level="DEBUG",
           rotation="10 MB",
           compression="zip")


def net_use_drive():
    try:
        if Path('{}:\\'.format(SETTINGS["drive"])).exists():
            return None
    except Exception as error:
        logger.error(error)
    while True:
        try:
            os.system('cmd /c net use {}: {}'.format(SETTINGS["drive"],
                                                     SETTINGS["connect_path"]))
            if Path('{}:\\'.format(SETTINGS["drive"])).exists():
                logger.info("Диск {} примонтирован успешно".format(
                    SETTINGS["drive"]))
                break
            else:
                try:
                    time.sleep(5)
                    os.system('cmd /c "net use {}: /del"'.format(
                        SETTINGS["drive"]))
                    time.sleep(5)
                except Exception as error:
                    logger.error(error)
        except Exception as error:
            logger.error(error)
            try:
                time.sleep(5)
                os.system('cmd /c "net use {}: /del"'.format(
                    SETTINGS["drive"]))
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
            if path_file.is_file():
                for path_arh in schema["arh"]:
                    new_path = Path(path_arh).joinpath(path_file.name)
                    shutil.copy(path_file, new_path)
                    logger.info("Файл {} скопирован в {}".format(
                        path_file, new_path))
                new_path = Path(schema["move"]).joinpath(path_file.name)
                shutil.copy(path_file, new_path)
                path_file.unlink()
                file_list.append(path_file.name)
                logger.info("Файл {} перемещен в {}".format(
                    path_file, new_path))
        if file_list and schema.get("log"):
            path_log = schema["log"]
            con = check_db_and_get_con(path_log)
            now_date = datetime.now()
            data = list(map(lambda x: (x, 0, now_date),
                            [x for x in file_list]))
            with con:
                try:
                    con.executemany(SQL_INSERT_LOGS, data)
                    logger.debug("Записи добавлены в базу")
                except Exception as error:
                    logger.error(
                        "Ошибка при добавлении в базу: {}".format(error))


async def monitoring() -> None:
    while True:
        start()
        await asyncio.sleep(SETTINGS["tics"])


if __name__ == "__main__":
    try:
        SETTINGS = load_settings(file_name='spfs_settings.json', log=False)
    except Exception as error:
        logger.error(
            "Ошибка при загрузке spfs_settings.json: {}".format(error))
    res = os.system('cmd /c "net use {}: /del"'.format(SETTINGS["drive"]))
    if res == 2:
        logger.error("Не удалось удалить диск {}".format(SETTINGS["drive"]))
    logger.debug("Запускаю мониторинг")
    try:
        asyncio.run(monitoring())
    except KeyboardInterrupt:
        logger.debug('Завершение работы программы!')
