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
