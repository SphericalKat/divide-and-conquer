from zipfile import ZipFile
from shutil import make_archive
import os


def zip_files(path: str, name: str):
    make_archive(name, "zip", path)


def unzip_archive(archive_path: str, extract_path: str):
    with ZipFile(archive_path, 'r') as archive:
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)
        archive.extractall(extract_path)
    os.remove(archive_path)


if __name__ == '__main__':
    zip_files(os.path.join('..', 'worktree'), 'test_archive')
    unzip_archive(os.path.join('test_archive.zip'), os.path.join('..', 'extract'))
