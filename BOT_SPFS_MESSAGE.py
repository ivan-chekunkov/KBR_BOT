import asyncio
import os
import sqlite3
import time

from pathlib import Path
from re import search

from loguru import logger

from settings import load as load_settings

version = "1.3"

SQL_REQ = """
    SELECT
        *
    FROM
        LOGS l
    WHERE
        l.cheked = 0
"""

SQL_UPDATE = """
    UPDATE
        LOGS
    SET
        cheked = 1
    WHERE
        id = ?
"""

logger.add(
    "Logfile.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="10 MB",
    compression="zip",
)


def net_use_drive():
    if not Path("{}:\\".format(SETTINGS["drive"])).exists():
        while True:
            try:
                res = os.system(
                    "cmd /c net use {}: {}".format(
                        SETTINGS["drive"], SETTINGS["connect_path"]
                    )
                )
                if res == 2:
                    logger.error(
                        "Не удалось примантировать диск {}".format(
                            SETTINGS["drive"]
                        )
                    )
                    os.system(
                        'cmd /c "net use {}: /del"'.format(SETTINGS["drive"])
                    )
                    time.sleep(10)
                    continue
            except Exception as error:
                logger.error(error)
                continue
            finally:
                break
        if Path("{}:\\".format(SETTINGS["drive"])).exists():
            logger.info(
                "Диск {} примонтирован успешно".format(SETTINGS["drive"])
            )


def _db_get_con(path: Path) -> sqlite3.Connection:
    while True:
        try:
            con = sqlite3.connect(path)
            return con
        except Exception as error:
            logger.error("Неудачный коннект к базе: {}".format(error))
            time.sleep(20)


def start():
    net_use_drive()
    con = _db_get_con(SETTINGS["db_path"])
    with con:
        data = list(con.execute(SQL_REQ))
        names_file = [x[1] for x in data]
        if not names_file:
            return
        id_records = map(lambda x: (x,), [x[0] for x in data])
        con.executemany(SQL_UPDATE, id_records)
        message = f"Количество файлов по СПФС для загрузки: {len(names_file)}"
        logger.info(message)
        for ip in SETTINGS["ip_admin"]:
            os.system('cmd /c "msg * /server:{} {}"'.format(ip, message))
        regex = SETTINGS["regex"]
        f_names = list(filter(lambda x: search(regex, x), names_file))
        if f_names:
            message = f"Количество файлов по СПФС для загрузки: {len(f_names)}"
            for ip in SETTINGS["ip_user"]:
                os.system('cmd /c "msg * /server:{} {}"'.format(ip, message))


async def monitoring() -> None:
    while True:
        start()
        await asyncio.sleep(SETTINGS["tics"])


if __name__ == "__main__":
    logger.debug("Запуск скрипта версии: {}".format(version))
    try:
        SETTINGS = load_settings(
            file_name="spfs_settings_message.json", log=False
        )
    except Exception as error:
        logger.error(
            "Ошибка при загрузке spfs_settings_message.json: {}".format(error)
        )
    res = os.system('cmd /c "net use {}: /del"'.format(SETTINGS["drive"]))
    if res == 2:
        logger.error("Не удалось удалить диск {}".format(SETTINGS["drive"]))
    logger.debug("Запускаю мониторинг")
    try:
        asyncio.run(monitoring())
    except KeyboardInterrupt:
        logger.debug("Завершение работы программы!")
