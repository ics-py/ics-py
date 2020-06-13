import warnings
from os import PathLike
from pathlib import Path
from typing import Dict, Iterable, Optional

__all__ = ["get_zoneinfo_dir", "get_windows_zone_mapping", "windows_to_olson", "is_vtimezone_ics_file",
           "get_vtimezone_files", "get_tzid_from_path", "find_file_for_tzid"]

PACKAGE_DIR: Path
ZONEINFO_DIR: Path
WINDOWS_ZONE_MAPPING_FILE: Path
WINDOWS_ZONE_MAPPING: Dict[str, str]


def __load():
    import json
    import importlib_resources  # type: ignore
    global PACKAGE_DIR, ZONEINFO_DIR, WINDOWS_ZONE_MAPPING_FILE, WINDOWS_ZONE_MAPPING
    try:
        if PACKAGE_DIR: return
    except NameError:
        pass

    PACKAGE_DIR = importlib_resources.files(__name__)
    ZONEINFO_DIR = PACKAGE_DIR.joinpath("zoneinfo")
    with PACKAGE_DIR.joinpath("windows_zone_mapping.json").open("r") as f:
        WINDOWS_ZONE_MAPPING = json.load(f)


def get_zoneinfo_dir() -> Path:
    __load()
    return ZONEINFO_DIR


def __maybe_zoneinfo_dir(dir: Optional[Path]) -> Path:
    if dir is None:
        return get_zoneinfo_dir()
    else:
        return dir


def get_windows_zone_mapping() -> Dict[str, str]:
    __load()
    return WINDOWS_ZONE_MAPPING


def windows_to_olson(win: str) -> Optional[str]:
    return get_windows_zone_mapping().get(win, None)


def is_vtimezone_ics_file(file: Path) -> bool:
    return file.exists() and file.is_file() and file.name.endswith(".ics")


def get_vtimezone_files(in_dir: Optional[Path] = None) -> Iterable[Path]:
    for f in __maybe_zoneinfo_dir(in_dir).iterdir():
        if f.is_dir():
            yield from get_vtimezone_files(f)
        elif is_vtimezone_ics_file(f):
            yield f
        elif f.name not in ["zones.h", "zones.tab"]:
            warnings.warn("ignoring unknown zoneinfo file %s" % f)


def get_tzid_from_path(file: Path, root_dir: Optional[Path] = None) -> str:
    if not is_vtimezone_ics_file(file):
        raise ValueError("path %s doesn't point to an ics file" % file)
    return file.relative_to(__maybe_zoneinfo_dir(root_dir)).as_posix()[:-4]


def find_file_for_tzid(tzid: str, root_dir: Optional[Path] = None) -> Optional[Path]:
    file = __maybe_zoneinfo_dir(root_dir).joinpath(tzid + ".ics")
    if is_vtimezone_ics_file(file):
        return file
    else:
        return None


def find_file_for_tzfile_path(file_path: PathLike, root_dir: Optional[Path] = None) -> Optional[Path]:
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    parts = file_path.parts
    root_dir = __maybe_zoneinfo_dir(root_dir)
    for i in range(len(parts)):
        file = root_dir.joinpath("/".join(parts[i:]) + ".ics")
        if root_dir in file.parents and is_vtimezone_ics_file(file):
            return file
    return None
