import argparse
import json
import os.path
from enum import Enum

import json2html

import src.common.utils as utils
from src.common.logger import get_logger

logger = get_logger(__name__)


"""
verify project 85 labels
"""
OUT_OF_FOCUS = "Out of focus"


class LabelCountError(Enum):
    No_Label_2D = 1
    No_Label_3D = 2
    Label_Count_Mismatch = 3


class LabelIDError(Enum):
    Invalid_ID_2D = 1,
    Invalid_ID_3D = 2,
    ID_Mismatch = 3


class LabelOutOfPlaceError(Enum):
    Invalid_Class_2D = 1,
    Invalid_Class_3D = 2


CAR = "car"
CHAIR = "chair"
COUNTER = "counter"
DESK = "desk"
DISPLAY_STAND = "display stand"
FENCE = "fence"
FIRE_EXTINGUISHER = "fire extinguisher"
INFORMATION_BOARD = "information board"
PERSON = "person"
PILLAR = "pillar"
SCULPTURE = "sculpture"
SIGN = "sign"
TABLE = "table"
WASTEBASKET = "wastebasket"


CLASS_PERSON = [PERSON]
PLACE_CLASSES_STATIC = {
    # restaurant Large
    "PL01": [COUNTER, TABLE, CHAIR, PILLAR, INFORMATION_BOARD],
    # exhibit hall
    "PL02": [SCULPTURE, PILLAR, WASTEBASKET, FIRE_EXTINGUISHER],
    # gym
    "PL03": [TABLE],
    # venue
    "PL04": [CHAIR, WASTEBASKET, FIRE_EXTINGUISHER],
    # underground mall
    "PL05": [CHAIR, PILLAR, FIRE_EXTINGUISHER],
    # indoor parking lot
    "PL06": [SIGN, CAR, PILLAR, FIRE_EXTINGUISHER],
    # supermarket
    "PL07": [DISPLAY_STAND, INFORMATION_BOARD, FIRE_EXTINGUISHER],
    # restaurant M
    "PL08": [TABLE, CHAIR, PILLAR, WASTEBASKET, FIRE_EXTINGUISHER],
    # bank
    "PL09": [CHAIR, PILLAR, WASTEBASKET, FIRE_EXTINGUISHER],
    # wedding hall
    "PL10": [SCULPTURE, TABLE, DESK, PILLAR, FIRE_EXTINGUISHER],
    # terminal
    "PL11": [SIGN, PILLAR, FIRE_EXTINGUISHER],
    # church
    "PL12": [TABLE, CHAIR, DESK, FENCE, FIRE_EXTINGUISHER],
}


def verify_project85_labels(path_in: str, path_out: str):
    label_files = utils.glob_files_all(path_in, file_type="*.json")
    logger.info(f"Found {len(label_files)} label_files")

    out_dir = os.path.dirname(path_out)
    if out_dir and not os.path.exists(out_dir):
        os.mkdir(out_dir)

    label_count_errors = []
    label_id_errors = []
    out_of_place_errors = []

    for label_file in label_files:
        logger.info(f"Processing {label_file}")
        label_data_json = utils.from_file(label_file)

        image = label_data_json.get("image")
        image_basename = os.path.basename(image.get("file_name"))
        if not image_basename:
            logger.error(f"empty image file name {image}")
            continue

        labels_2d = label_data_json.get("annotations")
        labels_3d = label_data_json.get("pcd_annotations")

        # 1. label count errors
        count_labels_2d = len(labels_2d)
        count_labels_3d = len(labels_3d)

        if count_labels_2d != count_labels_3d or count_labels_2d == 0 or count_labels_3d == 0:
            error_dict = dict()
            error_dict[image_basename] = {"2d_label_count": count_labels_2d,
                                          "3d_label_count": count_labels_3d}
            label_count_errors.append(error_dict)

        # 2. label ID errors
        anno_ids_2d = [str(anno.get("id")) for anno in labels_2d]
        anno_ids_3d = [str(anno.get("obj_id")) for anno in labels_3d]
        anno_ids_2d.sort()
        anno_ids_3d.sort()

        # 2D against 3D
        # key: image_name
        # value: {
        #    anno_ids_2d: [],
        #    anno_ids_3d: [],
        #    anno_id_errors: []
        # }
        label_id_error = dict()
        anno_id_errors = []
        for id_2d, anno_id_2d in enumerate(anno_ids_2d):
            if not anno_id_2d.isdigit():
                anno_id_errors.append(LabelIDError.Invalid_ID_2D.name)
            for id_3d, anno_id_3d in enumerate(anno_ids_3d):
                if not anno_id_3d.isdigit():
                    anno_id_errors.append(LabelIDError.Invalid_ID_3D.name)

                if id_2d == id_3d and anno_id_2d != anno_id_3d:
                    anno_id_errors.append(LabelIDError.ID_Mismatch.name)
        if len(anno_id_errors) > 0:
            label_id_error[image_basename] = {
                "anno_ids_2d": anno_ids_2d,
                "anno_ids_3d": anno_ids_3d,
                "anno_id_errors": anno_id_errors
            }
            label_id_errors.append(label_id_error)

        # logger.info(label_id_errors)

        # 3. out of place classes
        categories = label_data_json.get("categories")
        anno_names_2d = [categories[anno.get("category_id")].get("name") for anno in labels_2d]
        anno_names_3d = [anno.get("obj_type") for anno in labels_3d]

        anno_names_2d.sort()
        anno_names_3d.sort()

        tokens = image_basename.split('_')
        place = tokens[1]
        # logger.info(place)

        invalid_classes_2d = []
        valid_classes = PLACE_CLASSES_STATIC.get(place) + CLASS_PERSON
        for anno_name_2d in anno_names_2d:
            # skip OUT_OF_FOCUS
            if anno_name_2d == OUT_OF_FOCUS:
                continue
            if anno_name_2d not in valid_classes:
                invalid_classes_2d.append(anno_name_2d)

        invalid_classes_3d = []
        for anno_name_3d in anno_names_3d:
            if anno_name_3d not in valid_classes:
                invalid_classes_3d.append(anno_name_3d)

        if len(invalid_classes_2d) > 0 or len(invalid_classes_3d) > 0:
            out_of_place_errors.append({image_basename: {
                "anno_names_2d": anno_names_2d,
                "anno_names_3d": anno_names_3d,
                "invalid_classes_2d": invalid_classes_2d,
                "invalid_classes_3d": invalid_classes_3d
            }})

        # logger.info(out_of_place_errors)

    errors_data = {"file_count": len(label_files),
                   "label_count_errors": len(label_count_errors),
                   "label_id_errors": len(label_id_errors),
                   "out_of_place_errors": len(out_of_place_errors),
                   "label_count_error_details": label_count_errors,
                   "label_id_error_details": label_id_errors,
                   "out_of_place_error_details": out_of_place_errors}

    json_data = json.dumps(errors_data, default=utils.default, ensure_ascii=False, indent=2)
    # logger.info(f"{json_data} {path_out}")
    utils.to_file(json_data, path_out)

    html = json2html.json2html.convert(json = json_data)
    utils.to_file(html, path_out + ".html")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_in", action="store", dest="path_in", type=str)
    parser.add_argument("--path_out", action="store", dest="path_out", type=str)

    args = parser.parse_args()

    if not args.path_out:
        args.path_out = os.path.join(".", "verify85")
    verify_project85_labels(args.path_in, args.path_out)
