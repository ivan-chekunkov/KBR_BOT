import asyncio
import random
from pathlib import Path
import shutil


def create_files():
    for i in range(15):
        rand = "".join(map(str, [random.randint(0, 10) for _ in range(10)]))
        path = Path("new").joinpath(f"{i}_{rand}.txt")
        text = "".join(map(chr, [random.randint(50, 100) for _ in range(100)]))
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)


START_FILES = set()

WAIT_NEW_FILES = 0


def get_start_files():
    for path_file in Path("new").iterdir():
        START_FILES.add(path_file)


def get_new_files():
    path_files = set(Path("new").iterdir())
    return path_files - START_FILES


def move_files():
    global WAIT_NEW_FILES
    files = Path("in").iterdir()
    for path_file in files:
        shutil.copy(path_file, Path("out").joinpath(path_file.name))
        path_file.unlink()
        WAIT_NEW_FILES = WAIT_NEW_FILES + 1


def start():
    global WAIT_NEW_FILES
    print(WAIT_NEW_FILES)
    if WAIT_NEW_FILES > 0:
        print("Жду новых")
        new_files = get_new_files()
        WAIT_NEW_FILES = WAIT_NEW_FILES - len(new_files)
        for i in new_files:
            print(i)
            START_FILES.add(i)
    else:
        print("Не жду новых")
    move_files()


async def monitoring() -> None:
    while True:
        start()
        await asyncio.sleep(5)


if __name__ == "__main__":
    get_start_files()
    asyncio.run(monitoring())
