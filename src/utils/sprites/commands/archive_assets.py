import pathlib
from datetime import date
from os import path, remove
from shutil import make_archive

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import src
from src.utils.cli import CommandMeta

date_string = date.today()
project_root = pathlib.Path(src.__file__).parent.parent
target = project_root / "assets"


class Command(metaclass=CommandMeta):
    name = "archive_assets"

    @staticmethod
    def run(*args):
        archive()
        remove(f"assets-{date_string}.zip")


class GetAssetsCommand(metaclass=CommandMeta):
    name = "get_assets"

    @staticmethod
    def run(*args):
        file_title = get_assets()
        move_assets_to_assets_folder(file_title)


def get_assets():
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)

    file_list = drive.ListFile(
        {
            "q": "'{}' in parents and trashed=false".format(
                "1OBgwK3_UOvSPezZLzmA09-K5Wt4ZSWhx"
            )
        }
    ).GetList()

    file = file_list[-1]
    print(f'Downloading {file["title"]} file from GDrive to {project_root}')
    file.GetContentFile(file["title"])
    return file["title"]


def move_assets_to_assets_folder(file_title):
    pathlib.Path(project_root / file_title).rename(target / file_title)
    print(f"{file_title} moved to {target}")


def archive():
    # Create assets archive
    if path.exists(target):
        src = path.realpath(target)
        make_archive(f"assets-{date_string}", "zip", src)

    # Authentication with API
    gauth = GoogleAuth()
    drive = GoogleDrive(gauth)

    # Upload to Drive
    upload_file = f"assets-{date_string}.zip"
    gfile = drive.CreateFile({"parents": [{"id": "1OBgwK3_UOvSPezZLzmA09-K5Wt4ZSWhx"}]})
    gfile.SetContentFile(upload_file)
    gfile.Upload()
