import argparse
import json
import os.path

import src.common.utils as utils
from src.common.logger import get_logger

logger = get_logger(__name__)


"""
verify project 85 labels
"""


def verify_project85_labels(path_in: str, path_out: str):
    label_files = utils.glob_files_all(path_in, file_type="*.json")
    logger.info(f"Found {len(label_files)} label_files")

    if not os.path.exists(path_out):
        os.mkdir(path_out)

    label_count_errors = []
    label_id_errors = []
    out_of_place_errors = []

    for label_file in label_files:
        logger.info(f"Processing {label_file}")
        label_data_json = utils.from_file(label_file)

        labels_2d = label_data_json.get("annotations")
        labels_3d = label_data_json.get("pcd_annotations")
        count_labels_2d = len(labels_2d)
        count_labels_3d = len(labels_3d)

        if count_labels_2d != count_labels_3d or count_labels_2d == 0 or count_labels_3d == 0:
            image = label_data_json.get("image")
            if image.get("file_name"):
                error_dict = dict()
                error_dict[image.get("file_name")] = {"2d_label_count": count_labels_2d,
                                                      "3d_label_count": count_labels_3d}
                label_count_errors.append(error_dict)
            else:
                logger.error(f"empty image file name {image}")
        break

    errors_data = {"label_count_errors": label_count_errors,
                   "label_id_errors": label_id_errors,
                   "out_of_place_errors": out_of_place_errors}

    json_data = json.dumps(errors_data, default=utils.default, ensure_ascii=False, indent=2)
    logger.info(f"{json_data} {path_out}")
    utils.to_file(json_data, path_out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_in", action="store", dest="path_in", type=str)
    parser.add_argument("--path_out", action="store", dest="path_out", type=str)

    args = parser.parse_args()

    if not args.path_out:
        args.path_out = os.path.join(".", "verify85")
    verify_project85_labels(args.path_in, args.path_out)
