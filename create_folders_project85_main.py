import argparse
import os.path
import shutil as shutil

import src.common.utils as utils
from src.common.logger import get_logger

logger = get_logger(__name__)


"""
Create folders based on JSON filenames
"""
FOLDER_MAP = {
    "RB1": "RB1(4족보행로봇)",
    "RB2": "RB2(바퀴주행로봇)",

    "PL01": "PL01(대형식당)",
    "PL02": "PL02(전시장)",
    "PL03": "PL03(체육시설)",
    "PL04": "PL04(공연장)",
    "PL05": "PL05(지하상가)",
    "PL06": "PL06(실내주차장)",
    "PL07": "PL07(대형마트)",
    "PL08": "PL08(중형식당)",
    "PL09": "PL09(은행)",
    "PL10": "PL10(예식장)",
    "PL11": "PL11(터미널)",
    "PL12": "PL12(교회)",

    "D1": "D1(순환주행)",
    "D2": "D2(패턴주행)",
    "D3": "D3(지정주행)",

    "P1": "P1(수동조정자A)",
    "P2": "P2(수동조정자B)",
    "P3": "P3(수동조정자C)",
    "P4": "P4(수동조정자D)",
    
    "SN01": "SN01",
    "SN02": "SN02",
    "SN03": "SN03",
    "SN04": "SN04",
    "SN05": "SN05",
    "SN06": "SN06",
    "SN07": "SN07",
    "SN08": "SN08",
    "SN09": "SN09",
    "SN10": "SN10"
}


def create_folders(path_in: str, path_out: str):
    label_files = utils.glob_files_all(path_in, file_type="*.json")
    logger.info(f"Found {len(label_files)} label_files")

    out_dir = path_out
    if out_dir and not os.path.exists(out_dir):
        os.mkdir(out_dir)

    for idx, label_file in enumerate(label_files):
        parent_folder = os.path.basename(os.path.dirname(label_file))
        tokens = parent_folder.replace("_1_", "").split('_')
        # logger.info(tokens)

        out_sub_dir = out_dir
        for token in tokens:
            folder = FOLDER_MAP.get(token)
            if not folder:
                logger.error(f"Can't find file mapping for {token} {tokens} in {label_file}")

            out_sub_dir = os.path.join(out_sub_dir, folder)
            if not os.path.exists(out_sub_dir):
                os.mkdir(out_sub_dir)

        destination_file = os.path.join(out_sub_dir, os.path.basename(label_file))
        logger.info(f"Copying {idx+1}/{len(label_files)} {label_file} to {destination_file}")
        shutil.copy(label_file, destination_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_in", action="store", dest="path_in", type=str)
    parser.add_argument("--path_out", action="store", dest="path_out", type=str)

    args = parser.parse_args()

    if not args.path_out:
        args.path_out = os.path.join(".", "verify85")
    create_folders(args.path_in, args.path_out)
