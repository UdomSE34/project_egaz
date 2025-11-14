import zipfile
import os

zip_path = "media.zip"

if os.path.exists(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")
    print("Media ZIP extracted successfully.")
else:
    print("media.zip NOT found")
