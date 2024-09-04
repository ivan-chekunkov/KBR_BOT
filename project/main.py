import os

from loguru import logger

from settings import load as set_load

TEST = True

NAME_MODULE = os.path.basename(__file__).split(".")[0]

SETTINGS = {}


def _create_log():
    logger.add(
        "Logfile_{}.log".format(NAME_MODULE),
        format="{time} {level} {message}",
        level="DEBUG",
        rotation="10 MB",
        compression="zip",
    )


def func_1():
    print("func_1")


def func_2():
    print("func_2")


def func_3():
    print("func_3")


def func_4():
    print("func_4")


def settings_get_profile():
    PROFILES = {
        "KBR_MAIN": func_1,
        "KBR_MESSAGE": func_2,
        "SPFS_MAIN": func_3,
        "SPFS_MESSAGE": func_4,
    }
    settings_profile = SETTINGS.get("profile")
    logger.info(settings_profile)
    if settings_profile not in PROFILES:
        logger.error(
            "Неверный профиль. Укажите один из доступных:\n-> {}".format(
                "\n-> ".join(PROFILES.keys())
            )
        )


if __name__ == "__main__":
    if TEST:
        print("\nTEEEEEEEEESSSTT\n")
        import pprint
    _create_log()
    logger.info("Start!")
    SETTINGS = set_load()
    settings_get_profile()
