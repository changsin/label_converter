import argparse
import os.path

import src.common.utils as utils
from src.common.logger import get_logger
import csv
import codecs

logger = get_logger(__name__)


"""
convert csv files to unicode
"""


def csv_to_unicode(path_meta: str, path_out: str):
    files_meta = utils.glob_files_all(path_meta, file_type="*.csv")
    logger.info(files_meta)

    if not os.path.exists(path_out):
        os.mkdir(path_out)

    for file_path in files_meta:
        logger.info(f"{file_path}")
        with open(file_path, 'r') as file_in:
            logger.info(f"{path_out} {os.path.basename(file_path)}")
            unicode_file_path = os.path.join(path_out, os.path.basename(file_path))
            with codecs.open(unicode_file_path, 'w', encoding="utf-8") as file_out:
                csv_reader = csv.reader(file_in)
                file_out.write('\xfe\xff')
                for row in csv_reader:
                    if row:
                        file_out.write(str(row))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_meta", action="store", dest="path_meta", type=str)
    parser.add_argument("--path_out", action="store", dest="path_out", type=str)

    args = parser.parse_args()

    if not args.path_out:
        args.path_out = os.path.join(".", "meta")
    csv_to_unicode(args.path_meta, args.path_out)
