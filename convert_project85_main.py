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

MD_COLUMNS1 = ["site", "location", "date", "address", "floor", "door", "wall"]
MD_COLUMNS2 = ["weather", "temperature", "lumen", "decibel"]
MD_COLUMNS3 = ["robot_id", "scenario_id", "pilot_id", "driving_type"]
MD_COLUMNS4 = ["scenario_start_time", "scenario_end_time", "distance_traveled", "running_time", "raw_data_filename"]
METADATA_COLUMNS = MD_COLUMNS1 + MD_COLUMNS2 + MD_COLUMNS3 + MD_COLUMNS4

IMU_COLUMNS1 = ["Sequence", "gyroscope_orientation.x", "gyroscope_orientation.y"]
IMU_COLUMNS2 = ["gyroscope_orientation.z", "gyroscope_orientation.w"]
IMU_COLUMNS3 = ["magnetometer_angular_velocity.x", "magnetometer_angular_velocity.y", "magnetometer_angular_velocity.z"]
IMU_COLUMNS4 = ["accelerometer_linear_acceleration.x", "accelerometer_linear_acceleration.y"]
IMU_COLUMNS5 = ["accelerometer_linear_acceleration.z"]
IMU_COLUMNS = IMU_COLUMNS1 + IMU_COLUMNS2 + IMU_COLUMNS3 + IMU_COLUMNS4 + IMU_COLUMNS5


def find_path_3d(paths_3d: [], task_name: str):
    for path in paths_3d:
        cur_base_name = os.path.basename(path)
        # logger.info(f"cur_base_name: {cur_base_name}")
        if cur_base_name == task_name:
            return path


def load_csv_files(paths: [], task_name: str, data_type="Meta", columns=METADATA_COLUMNS):
    metadata_path = None
    for path in paths:
        cur_base_name = os.path.basename(path)
        # logger.info(f"cur_base_name: {cur_base_name}")
        if cur_base_name == task_name + data_type + ".csv":
            metadata_path = path
            break

    if metadata_path:
        csv_reader = Project85CsvReader()
        csv_reader.columns = columns
        metadata_dict = csv_reader.parse([metadata_path])
        # logger.info(metadata_dict)
        return metadata_dict[task_name + data_type + ".csv"]


def convert_project85_labels(path_2d: str, path_3d: str, path_meta: str, path_imu: str, path_out: str):

    logger.info(f"2D: {path_2d} 3D: {path_3d} Meta: {path_meta} IMU: {path_imu} Out: {path_out}")
    files_2d = utils.glob_files_all(path_2d, file_type="*.xml")
    logger.info(f"Found {len(files_2d)} 2D files")

    folders_3d = utils.glob_folders(path_3d, file_type="*")
    logger.info(f"Found {len(folders_3d)} 3D folders")

    files_meta = utils.glob_files_all(path_meta, file_type="*.csv")
    logger.info(f"Found {len(files_meta)} Meta files")

    files_imu = utils.glob_files_all(path_imu, file_type="*.csv")
    logger.info(f"Found {len(files_imu)} IMU files")

    if not os.path.exists(path_out):
        os.mkdir(path_out)

    errors = 0
    missing_3d_paths = []
    for file_2d in files_2d:
        logger.info(f"Processing {file_2d}")
        cvat_reader = CVATReader()
        parsed_dict = cvat_reader.parse([file_2d])
        data_labels = DataLabels.from_adq_labels(AdqLabels.from_json(parsed_dict))

        task_name = data_labels.meta_data["task"]["name"]
        logger.info(f"task_name: {task_name}")

        task_path_3d = find_path_3d(folders_3d, task_name)
        logger.info(f"Found 3D path: {task_path_3d}")
        if not task_path_3d:
            logger.error(f"ERROR: 3D path not found {task_path_3d}")
            missing_3d_paths.append(task_name)
            errors += 1
            continue

        metadata_dict = load_csv_files(files_meta, task_name, data_type="Meta", columns=METADATA_COLUMNS)
        # logger.info(metadata_dict)
        imu_dict = load_csv_files(files_imu, task_name, data_type="IMU", columns=IMU_COLUMNS)
        # logger.info(imu_dict)

        p85_writer = Project85Writer()
        p85_writer.write_85(data_labels, task_path_3d, metadata_dict, imu_dict, path_out)
        logger.info(f"Finished {task_name}")

    logger.info(f"All finished {len(files_2d)} with {errors} errors")
    if len(missing_3d_paths) > 0:
        logger.error(f"Missing 3d path tasks are: {missing_3d_paths}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--path_2d", action="store", dest="path_2d", type=str)
    parser.add_argument("--path_3d", action="store", dest="path_3d", type=str)
    parser.add_argument("--path_meta", action="store", dest="path_meta", type=str)
    parser.add_argument("--path_imu", action="store", dest="path_imu", type=str)
    parser.add_argument("--path_out", action="store", dest="path_out", type=str)

    args = parser.parse_args()

    if not args.path_out:
        args.path_out = os.path.join(".", "85out")
    convert_project85_labels(args.path_2d, args.path_3d, args.path_meta, args.path_imu, args.path_out)
