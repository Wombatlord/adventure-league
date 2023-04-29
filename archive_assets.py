from os import path
from shutil import make_archive
from datetime import date
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

date_string = date.today()

if path.exists("./assets"):
    src = path.realpath("./assets")
    make_archive(f"assets-{date_string}","zip",src)

gauth = GoogleAuth()           
drive = GoogleDrive(gauth)

upload_file = f'assets-{date_string}.zip' 

gfile = drive.CreateFile({'parents': [{'id': '1OBgwK3_UOvSPezZLzmA09-K5Wt4ZSWhx'}]})
# Read file and set it as the content of this instance.
gfile.SetContentFile(upload_file)
gfile.Upload() # Upload the file.
