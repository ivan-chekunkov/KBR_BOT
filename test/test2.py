import asyncio
import random
import time
import os

from pathlib import Path

from loguru import logger

from settings import load as load_settings


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


def create_files():
    net_use_drive()
    for i in range(15):
        rand = "".join(map(str, [random.randint(0, 10) for _ in range(10)]))
        path = Path(SETTINGS["base"]).joinpath(f"{i}_{rand}.txt")
        text = "".join(map(chr, [random.randint(50, 100) for _ in range(100)]))
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        logger.info("Файл {} создан!".format(path))


async def monitoring() -> None:
    while True:
        create_files()
        await asyncio.sleep(SETTINGS["tics"])


def _exit():
    logger.debug("Завершение работы программы!")
    res = _del_drive()
    if res == 2:
        logger.error("Не удалось удалить диск {}".format(SETTINGS["drive"]))


if __name__ == "__main__":
    try:
        SETTINGS = load_settings(file_name="test_settings.json", log=False)
    except Exception as error:
        logger.error(
            "Ошибка при загрузке test_settings.json: {}".format(error)
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
    print(SETTINGS)
    try:
        # asyncio.run(monitoring())
        print(SETTINGS)
    except KeyboardInterrupt:
        _exit()
