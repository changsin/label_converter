import json
import os.path
from pathlib import Path

import src.common.utils as utils
from src.common.constants import SUPPORTED_LABEL_FILE_EXTENSIONS
from src.common.logger import get_logger
from src.models.data_labels import DataLabels
from .base_writer import BaseWriter
from .project85_csv_reader import Project85CsvReader

logger = get_logger(__name__)


class Project85Writer(BaseWriter):
    def __init__(self):
        super().__init__()
        self.categories = dict()

    @staticmethod
    def _get_class_attribute_name(meta_data_dict: dict):
        search_str = "task/labels/label/attributes/attribute/name"
        return utils.get_dict_value(meta_data_dict, search_str)
    # def _get_class_attribute_name(meta_data_dict: dict):
    #     search_str = "task/labels/label/attributes/attribute/name"
    #     return utils.get_dict_value(meta_data_dict, search_str)

    def _parse_class_names(self, meta_data_dict: dict):
        search_str = "task/labels/label"
        labels = utils.get_dict_value(meta_data_dict, search_str)

        classes = []
        for idx, label_dict in enumerate(labels):
            clazz = label_dict.get("name")
            category_dict = dict()
            category_dict['id'] = idx
            category_dict['name'] = clazz
            # category_dict['supercategory'] = ""

            classes.append(category_dict)
            self.categories[clazz] = idx

        return classes

    def write(self, file_in: str, file_out: str):
        pass

    def write_85(self, data_labels: DataLabels, path_3d: str, current_metadata_dict: dict, path_out: str) -> None:
        def _create_converted_json(metadata_dict):
            """
            create the template for the converted json
            """
            converted_json = dict()

            licenses = []
            default_license = dict()
            # TODO: hard-coding it for now
            default_license["name"] = "blackolive"
            default_license["id"] = 0
            default_license["url"] = "https://bo.testworks.ai/"

            licenses.append(default_license)

            converted_json["licenses"] = licenses

            info_dict = dict()
            info_dict["description"] = utils.get_dict_value(data_labels.meta_data, "task/project")
            info_dict["date_created"] = utils.get_dict_value(data_labels.meta_data, "task/created")

            if metadata_dict:
                env_dict = dict()
                env_dict["site"] = metadata_dict["site"]
                env_dict["location"] = metadata_dict["location"]
                env_dict["date"] = metadata_dict["date"]
                env_dict["weather"] = metadata_dict["weather"]
                env_dict["temperature"] = metadata_dict["temperature"]
                env_dict["lumen"] = metadata_dict["lumen"]
                # TODO: was "noise"
                env_dict["decibel"] = metadata_dict["decibel"]
                # TODO: was "material"
                env_dict["floor_material"] = metadata_dict["floor"]
                info_dict["env"] = env_dict

            converted_json["info"] = info_dict

            if data_labels.meta_data:
                converted_json["categories"] = self._parse_class_names(data_labels.meta_data)

            return converted_json

        cuboid_filenames = utils.glob_files(path_3d, file_type="*.json")
        cuboid_filenames.sort()

        for idx, image in enumerate(data_labels.images):
            converted_json = _create_converted_json(current_metadata_dict)

            # 1. images
            converted_images = []
            converted_image = dict()
            converted_image["id"] = int(image.image_id)
            converted_image["width"] = image.width
            converted_image["height"] = image.height
            converted_image["file_name"] = image.name

            # 1-1 Add scenario info if metadata are available
            if current_metadata_dict:
                scenario_dict = dict()
                scenario_dict["id"] = current_metadata_dict["scenario_id"]
                scenario_dict["start_time"] = current_metadata_dict["scenario_start_time"]
                scenario_dict["end_time"] = current_metadata_dict["scenario_end_time"]
                scenario_dict["distance_traveled"] = current_metadata_dict["distance_traveled"]
                scenario_dict["len"] = len(data_labels.images)
                scenario_dict["index"] = idx

                converted_image["scenario"] = scenario_dict

            converted_images.append(converted_image)

            # 2. Add annotations
            converted_annotations = []
            annotation_id = 0
            if image.objects:
                for anno_object in image.objects:
                    annotation = dict()
                    annotation["id"] = int(anno_object.attributes["ID"])
                    annotation["image_id"] = int(image.image_id)
                    class_name = anno_object.label
                    annotation["category_id"] = self.categories[class_name]
                    annotation_id += 1

                    annotation["bbox"] = anno_object.points[0]

                    is_social_interaction = anno_object.attributes.get("Interaction")
                    if is_social_interaction:
                        attributes_dict = dict()
                        attributes_dict["is_social_interaction"] = False if is_social_interaction == "off" else True
                        annotation["attributes"] = attributes_dict

                    converted_annotations.append(annotation)

            converted_json["images"] = converted_images
            converted_json["annotations"] = converted_annotations

            # 3. pcd_images
            # logger.info(f"## idx is {idx}/{len(cuboid_filenames)}")
            image_filename_stem = Path(image.name).stem
            filename_tokens = image_filename_stem.split('_')
            pcd_filename = Path(image.name).stem + ".pcd"

            pcd_images = []

            pcd_image_dict = dict()
            pcd_image_dict["id"] = int(image.image_id)
            pcd_image_dict["file_name"] = pcd_filename
            pcd_image_dict["license"] = 0
            pcd_image_dict["date_capture"] = utils.get_dict_value(data_labels.meta_data, "task/created")
            pcd_images.append(pcd_image_dict)

            converted_json["pcd_images"] = pcd_images

            # 4. pc_annotations
            # TODO: have to remove extra "00" from cuboid filenames
            cuboid_anno_filename = os.path.join(path_3d, "00" + filename_tokens[-1] + ".json")
            converted_json["pcd_annotations"] = []
            if cuboid_anno_filename in cuboid_filenames:
                cuboid_labels = utils.from_file(cuboid_anno_filename)
                converted_json["pcd_annotations"] = cuboid_labels

            # 5. write out the converted json to a file
            json_data = json.dumps(converted_json, default=utils.default, ensure_ascii=False, indent=2)

            task_name = data_labels.meta_data["task"]["name"]
            output_folder = os.path.join(path_out, task_name)
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)

            output_filename = os.path.join(output_folder, image_filename_stem + ".json")
            utils.to_file(json_data, output_filename)


