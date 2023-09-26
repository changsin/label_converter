import argparse
import os.path

import src.common.utils as utils
from src.common.logger import get_logger
from src.converters.cvat_reader import CVATReader
from src.converters.project85_csv_reader import Project85CsvReader
from src.converters.project85_writer import Project85Writer
from src.models.adq_labels import AdqLabels
from src.models.data_labels import DataLabels

logger = get_logger(__name__)


"""
convert label files into different formats
"""


def find_path_3d(paths_3d: [], task_name: str):
    for path in paths_3d:
        cur_base_name = os.path.basename(path)
        # logger.info(f"cur_base_name: {cur_base_name}")
        if cur_base_name == task_name:
            return path


def load_metadata(paths_metadata: [], task_name: str):
    metadata_path = None
    for path in paths_metadata:
        cur_base_name = os.path.basename(path)
        # logger.info(f"cur_base_name: {cur_base_name}")
        if cur_base_name == task_name + "Meta.csv":
            metadata_path = path
            break

    if metadata_path:
        csv_reader = Project85CsvReader()
        metadata_dict = csv_reader.parse([metadata_path])
        # logger.info(metadata_dict)
        return metadata_dict[task_name + "Meta.csv"]


def convert_project85_labels(path_2d: str, path_3d: str, path_meta: str, path_out: str):

    logger.info(f"2D: {path_2d} 3D: {path_3d} Meta: {path_meta} Out: {path_out}")
    files_2d = utils.glob_files_all(path_2d, file_type="*.xml")
    logger.info(files_2d)

    folders_3d = utils.glob_folders(path_3d, file_type="*")
    logger.info(folders_3d)

    files_meta = utils.glob_files_all(path_meta, file_type="*.csv")
    logger.info(files_meta)

    if not os.path.exists(path_out):
        os.mkdir(path_out)

    for file_2d in files_2d:
        cvat_reader = CVATReader()
        parsed_dict = cvat_reader.parse([file_2d])
        data_labels = DataLabels.from_adq_labels(AdqLabels.from_json(parsed_dict))

        task_name = data_labels.meta_data["task"]["name"]
        # logger.info(task_name)

        task_path_3d = find_path_3d(folders_3d, task_name)
        # logger.info(f"Found 3D path: {task_path_3d}")

        metadata_dict = load_metadata(files_meta, task_name)
        # logger.info(metadata_dict)

        p85_writer = Project85Writer()
        p85_writer.write_85(data_labels, task_path_3d, metadata_dict, path_out)
        logger.info(f"Finished {task_name}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_2d", action="store", dest="path_2d", type=str)
    parser.add_argument("--path_3d", action="store", dest="path_3d", type=str)
    parser.add_argument("--path_meta", action="store", dest="path_meta", type=str)
    parser.add_argument("--path_out", action="store", dest="path_out", type=str)

    args = parser.parse_args()

    if not args.path_out:
        args.path_out = os.path.join(".", "85out")
    convert_project85_labels(args.path_2d, args.path_3d, args.path_meta, args.path_out)
