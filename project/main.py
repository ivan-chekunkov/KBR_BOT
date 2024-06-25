import os

from loguru import logger

import settings

logger.add(
    "Logfile_{}.log".format(os.path.basename(__file__).split(".")[0]),
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="10 MB",
    compression="zip",
)

if __name__ == "__main__":
    logger.info("WAW")
    settings.load()
