import glob
import json
import os
import zipfile
from pathlib import Path

import chardet


def default(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def from_file(filename, default_json="{}"):
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        file = open(filename, 'r', encoding='utf-8')
        return json.load(file)

    return json.loads(default_json)


def to_file(data, filename):
    """
    save data to path
    """
    with open(filename, 'w', encoding="utf-8") as json_file:
        json_file.write(data)


def glob_files(folder, file_type='*'):
    search_string = os.path.join(folder, file_type)
    files = glob.glob(search_string)

    # print('Searching ', search_string)
    paths = []
    for f in files:
      if os.path.isdir(f):
        sub_paths = glob_files(f + '/')
        paths += sub_paths
      else:
        paths.append(f)

    # We sort the images in alphabetical order to match them
    #  to the annotation files
    paths.sort()

    return paths


def glob_folders(folder, file_type='*'):
    search_string = os.path.join(folder, file_type)
    paths = glob.glob(search_string)

    # print('Searching ', search_string)
    folders_found = []
    for p in paths:
        if os.path.isdir(p):
            folders_found.append(p)

    folders_found.sort()

    return folders_found


def glob_files_all(path, file_type='*'):
    if not os.path.isdir(path):
        return [path]

    files = []
    # print("Searching {}".format(path))
    folders_found = glob_folders(path)
    # print("Found {} sub folders".format(len(folders_found)))

    if not folders_found:
        folders_found = [path]

    for sub_folder in folders_found:
        tmp_files = glob_files(sub_folder, file_type)
        files.extend(tmp_files)
    # print("Found {} files".format(len(files)))
    return files

# def glob_files(folder_path, patterns="*"):
#     matched = []
#     for pattern in patterns:
#         print(os.path.join(folder_path, '*.' + pattern))
#         globbed = glob.glob(os.path.join(folder_path, '*.' + pattern))
#         if globbed:
#             matched.extend(globbed)
#
#     return matched


def from_text_file(text_file):
    return Path(text_file).read_text()


def get_dict_value(meta_data_dict: dict, search_str: str):
    cur_dict = meta_data_dict
    level_name_tokens = search_str.split('/')
    for token in level_name_tokens:
        if isinstance(cur_dict, list):
            cur_dict = cur_dict[0].get(token)
        else:
            cur_dict = cur_dict.get(token)

    return cur_dict


# Function to zip a folder
def zip_folder(folder_path, zip_filename):
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)


def get_encoding(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        encode = chardet.detect(data)
        return encode.get("encoding")


def seconds_to_hhmmss(seconds: int):
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
