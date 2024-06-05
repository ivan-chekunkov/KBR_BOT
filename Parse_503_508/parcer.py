import base64
import sys
import xml.etree.ElementTree as ETree

from re import search as re_search
from pathlib import Path
from typing import Callable

from loguru import logger

from settings import load as load_settings

regex_503 = r"6015078000ED503.*"
regex_508 = r"6015078000ED508.*"
regex_201 = r"6015078000ED201.*"

logger.add('Logfile.log',
           format="{time} {level} {message}",
           level="DEBUG",
           rotation="10 MB",
           compression="zip")


def _iter_dir(path: Path) -> list[Path]:
    return path.iterdir()


def parcer_508(path: Path) -> None:
    data = ""
    for root in ETree.parse(path).getroot():
        if root.tag == "{urn:cbr-ru:dsig:env:v1.1}Object":
            data = root.text
    if not data:
        logger.error("ERROR not <Object> in XML")
        return None
    try:
        xml_object = base64.b64decode(data).decode("utf-8")
    except UnicodeDecodeError:
        xml_object = base64.b64decode(data).decode("cp1251")
    tree = ETree.fromstring(xml_object)
    result = tree.attrib
    result["error"] = ""
    for branch in tree:
        if branch.tag == "{urn:cbr-ru:ed:v2.0}EDRefID":
            for key, val in branch.attrib.items():
                key = key + "_1"
                result[key] = val
        if branch.tag == "{urn:cbr-ru:ed:v2.0}SWIFTDocCtrlInfo":
            if "SWIFTCtrlCode" in branch.attrib:
                print_error(f"В {path} есть сообщение об ошибке!!!")
            result.update(branch.attrib)
            try:
                for i in branch:
                    if i.tag == "{urn:cbr-ru:ed:v2.0}Annotation":
                        result["error"] = result["error"] + "\n" + i.text
                    if i.tag == "{urn:cbr-ru:ed:v2.0}SWIFTErrCodeList":
                        error = f"{i.attrib} = {''.join([x.text for x in i])}"
                        result["error"] = result["error"] + "\n" + error
            except Exception as error:
                logger.error(error)
    if result.get("error"):
        result["FAIL"] = "ERROR_"
    else:
        result["FAIL"] = ""
    with open("pattern_508.txt", "r", encoding="cp1251") as file:
        pattern = file.read()
    name_out_file = Path(SETTINGS["files_out"]).joinpath(
        "{FAIL}{EDDate}_{SenderSWIFTBIC}_{EDNo}_508.txt".format(**result))
    with open(name_out_file, "w", encoding="utf-8") as file:
        file.write(pattern.format(**result))
    if result.get("error"):
        logger.error(f"Файл: {path} - обработан!")
    else:
        logger.info(f"Файл: {path} - обработан!")


def parcer_503(path: Path) -> None:
    data = ""
    for root in ETree.parse(path).getroot():
        if root.tag == "{urn:cbr-ru:dsig:env:v1.1}Object":
            data = root.text
    if not data:
        logger.error("ERROR not <Object> in XML")
        return None
    try:
        xml_object = base64.b64decode(data).decode("utf-8")
    except UnicodeDecodeError:
        xml_object = base64.b64decode(data).decode("cp1251")
    tree = ETree.fromstring(xml_object)
    result = tree.attrib
    if result.get("IsNotice"):
        result["IsNotice"] = ("Да" if result.get("IsNotice").lower() == "true"
                              else "Нет")
    for key, val in tree[2].attrib.items():
        key = key + "_1"
        result[key] = val
    result.update(tree[1].attrib)
    try:
        result["swift"] = base64.b64decode(tree[1][0].text).decode("utf-8")
    except UnicodeDecodeError:
        result["swift"] = base64.b64decode(tree[1][0].text).decode("cp1251")
    result["swift"] = result["swift"].replace("\r", "")
    with open("pattern_503.txt", "r", encoding="cp1251") as file:
        pattern = file.read()
    name_out_file = Path(SETTINGS["files_out"]).joinpath(
        "{EDDate}_{SenderSWIFTBIC}_{EDNo}_{FormatType}.txt".format(**result))
    with open(name_out_file, "w", encoding="utf-8") as file:
        file.write(pattern.format(**result))
    logger.info(f"Файл: {path} - обработан!")


def parcer_201(path: Path) -> None:
    data = ""
    for root in ETree.parse(path).getroot():
        if root.tag == "{urn:cbr-ru:dsig:env:v1.1}Object":
            data = root.text
    if not data:
        logger.error("ERROR not <Object> in XML")
        return None
    try:
        xml_object = base64.b64decode(data).decode("utf-8")
    except UnicodeDecodeError:
        xml_object = base64.b64decode(data).decode("cp1251")
    tree = ETree.fromstring(xml_object)
    error = []
    result = tree.attrib
    for branch in tree:
        if branch.tag == "{urn:cbr-ru:ed:v2.0}Annotation":
            error.append(branch.text)
        if branch.tag == "{urn:cbr-ru:ed:v2.0}ErrorDiagnostic":
            error.append(branch.text)
    if not error:
        logger.error("Не смог найти ошибку в файле")
        return None
    result["error"] = "\n".join(error)
    with open("pattern_201.txt", "r", encoding="cp1251") as file:
        pattern = file.read()
    name_out_file = Path(SETTINGS["files_out"]).joinpath(
        "ERROR_{EDDate}_{EDNo}_201.txt".format(**result))
    with open(name_out_file, "w", encoding="utf-8") as file:
        file.write(pattern.format(**result))
    logger.error(f"Файл: {path} - обработан!")


def _unlink_file(path: Path) -> None:
    path.unlink()
    logger.info(f"Файл: {path} - удалён!")


def _queue_files(*args: list[Path], func: Callable) -> None:
    for paths in args:
        for path in paths:
            try:
                func(path)
            except Exception as error:
                print_error(f"ОШИБКА ПРИ ОБРАБОТКЕ ФАЙЛА {path}")
                print_error(error)


def _split_files(
        paths: list[Path]) -> tuple[list[Path], list[Path], list[Path]]:
    file_503 = []
    file_508 = []
    file_201 = []
    for_del = []
    for path in paths:
        if re_search(regex_503, path.name):
            file_503.append(path)
            continue
        if re_search(regex_508, path.name):
            file_508.append(path)
            continue
        if re_search(regex_201, path.name):
            file_201.append(path)
            continue
        for_del.append(path)
    return file_503, file_508, for_del, file_201


def print_error(text: str) -> None:
    logger.error(f'\n{"=" * 30}\n{text}\n{"=" * 30}')


if __name__ == "__main__":
    try:
        SETTINGS = load_settings("settings.json", log=True, handler="f")
        logger.debug("Файл с настройками 'settings.json' загружен")
    except Exception as error:
        logger.error("Ошибка при загрузке файла с настройками 'settings.json'")
        logger.error(error)
    paths_503, paths_508, for_del, paths_201 = _split_files(
        _iter_dir(Path(SETTINGS["files_in"])))
    _queue_files(paths_503, func=parcer_503)
    _queue_files(paths_508, func=parcer_508)
    _queue_files(paths_201, func=parcer_201)
    if not (len(sys.argv) > 1 and sys.argv[1].lower() == "save"):
        _queue_files(
            for_del,
            paths_503,
            paths_508,
            paths_201,
            func=_unlink_file,
        )
    if paths_201:
        print_error("Есть файлы с ошибками 201!!!!!!")
