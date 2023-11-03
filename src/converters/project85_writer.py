import json
import os.path
from pathlib import Path

import src.common.utils as utils
from src.common.logger import get_logger
from src.models.data_labels import DataLabels
from .base_writer import BaseWriter

logger = get_logger(__name__)

INTERVAL = 3    # seconds
OUT_OF_FOCUS = "Out of focus"


class Project85Writer(BaseWriter):
    def __init__(self):
        super().__init__()
        # key: id, value: name
        self.categories = dict()
        # a list of true/false indicating if there is any interaction for the given image
        # key: image_id, value: true/false
        self.social_interactions = dict()
        self.interaction_start_time = None
        self.interaction_end_time = None

        # key: image_id, value: true/false
        self.out_of_focus = dict()

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

    def _convert_annotation_dict(self, anno_dict, image_id):
        annotation = dict()
        annotation_id = anno_dict.attributes["ID"]
        annotation["id"] = annotation_id
        if annotation_id and annotation_id.isdigit():
            annotation["id"] = int(annotation_id)
        else:
            logger.error(f"\t\tInvalid annotation_id {annotation_id}")
            # annotation["id"] = -1

        annotation["image_id"] = image_id
        class_name = anno_dict.label
        annotation["category_id"] = self.categories[class_name]

        annotation["bbox"] = anno_dict.points[0]

        is_social_interaction = anno_dict.attributes.get("Interaction")
        if is_social_interaction:
            attributes_dict = dict()
            social_interaction_flag = False if is_social_interaction == "off" else True
            attributes_dict["is_social_interaction"] = social_interaction_flag
            annotation["attributes"] = attributes_dict

        return annotation

    def _create_info_dict(self, description, metadata_dict: dict, imu_dict: dict):
        info_dict = dict()
        info_dict["description"] = description
        info_dict["date_created"] = metadata_dict["date"]

        if metadata_dict:
            env_dict = dict()
            env_dict["site"] = metadata_dict["site"]
            env_dict["location"] = metadata_dict["location"]
            env_dict["date"] = metadata_dict["date"]
            env_dict["weather"] = metadata_dict["weather"]
            env_dict["temperature"] = float(metadata_dict["temperature"])
            env_dict["lumen"] = float(metadata_dict["lumen"])
            env_dict["decibel"] = float(metadata_dict["decibel"])
            env_dict["floor_material"] = metadata_dict["floor"]
            env_dict["gate_material"] = metadata_dict["door"]
            env_dict["wall_material"] = metadata_dict["wall"]

            env_dict["running_time"] = metadata_dict["running_time"]
            if self.interaction_start_time and self.interaction_end_time:
                env_dict["interaction_start_time"] = self.interaction_start_time
                env_dict["interaction_end_time"] = self.interaction_end_time

            info_dict["env"] = env_dict

        if imu_dict:
            info_dict["imu"] = imu_dict

        return info_dict

    def _parse_social_interactions(self, data_labels: DataLabels):
        # go through all images and labels and mark off social interaction intervals based on image_id
        for idx, image in enumerate(data_labels.images):
            for anno_object in image.objects:
                image_id = int(image.image_id)

                if anno_object.label == OUT_OF_FOCUS:
                    logger.info("## out of focus detected")
                    self.out_of_focus[image_id] = True

                is_social_interaction = anno_object.attributes.get("Interaction")
                if is_social_interaction:
                    social_interaction_flag = False if is_social_interaction == "off" else True

                    if social_interaction_flag:
                        social_interaction_recorded = self.social_interactions.get(image_id)
                        if not social_interaction_recorded:
                            self.social_interactions[image_id] = social_interaction_flag
                            # logger.info(f"## social_interactions: {self.social_interactions}")
        # self.social_interactions should now have { image_id: true }
        # now go through self.social_interactions to find interaction_start_time and interaction_end_time

        start_idx, end_idx = -1, -1
        for image_id, is_interaction in self.social_interactions.items():
            if is_interaction:
                # logger.info(f"is_interaction: {image_id} {is_interaction} {start_idx} {end_idx}")
                if start_idx == -1:
                    start_idx = image_id
                    end_idx = image_id

                if image_id > start_idx and image_id > end_idx:
                    end_idx = image_id

        if start_idx != -1 and end_idx != -1:
            start_time = (start_idx + 1) * INTERVAL
            end_time = (end_idx + 2) * INTERVAL

            self.interaction_start_time = utils.seconds_to_hhmmss(start_time)
            self.interaction_end_time = utils.seconds_to_hhmmss(end_time)
            # logger.info(f"### {self.interaction_start_time} {self.interaction_end_time}")

    def write_85(self, data_labels: DataLabels, path_3d: str,
                 current_metadata_dict: dict, imu_dict: dict, path_out: str) -> None:
        def _create_converted_json():
            """
            create the template for the converted json
            """
            converted_json = dict()

            default_license = dict()
            # TODO: hard-coding it for now
            default_license["name"] = "blackolive"
            default_license["id"] = 0
            default_license["url"] = "https://bo.testworks.ai/"

            converted_json["license"] = default_license

            info_dict = self._create_info_dict(utils.get_dict_value(data_labels.meta_data, "task/project"),
                                               current_metadata_dict, imu_list[idx])
            converted_json["info"] = info_dict

            if data_labels.meta_data:
                converted_json["categories"] = self._parse_class_names(data_labels.meta_data)

            return converted_json

        imu_list = []
        keys = imu_dict.keys()
        for idx in range(len(imu_dict["Sequence"])):
            temp_dict = dict()
            for key in keys:
                if key != "Sequence":
                    temp_dict[key] = float(imu_dict[key][idx])
            imu_list.append(temp_dict)

        cuboid_filenames = utils.glob_files(path_3d, file_type="*.json")
        cuboid_filenames.sort()

        self._parse_social_interactions(data_labels)

        for idx, image in enumerate(data_labels.images):
            converted_json = _create_converted_json()

            task_name = data_labels.meta_data["task"]["name"]
            image_filename = image.name
            if image_filename.find(task_name) == -1:
                image_filename = task_name + image_filename

            # 1. images
            image_id = int(image.image_id)
            converted_image = dict()
            converted_image["id"] = image_id
            converted_image["width"] = image.width
            converted_image["height"] = image.height
            converted_image["file_name"] = image_filename
            if self.out_of_focus.get(image_id):
                converted_image["out_of_focus"] = self.out_of_focus[image_id]

            # 1-1 Add scenario info if metadata are available
            if current_metadata_dict:
                scenario_dict = dict()
                scenario_dict["id"] = current_metadata_dict["scenario_id"]
                scenario_dict["start_time"] = current_metadata_dict["scenario_start_time"]
                scenario_dict["end_time"] = current_metadata_dict["scenario_end_time"]
                scenario_dict["distance_traveled"] = float(current_metadata_dict["distance_traveled"])
                scenario_dict["len"] = len(data_labels.images)
                scenario_dict["index"] = idx

                converted_image["scenario"] = scenario_dict

            # 2. Add annotations
            converted_annotations = []

            # logger.info(f"\tprocessing {image_filename}")
            if image.objects:
                for anno_object in image.objects:
                    annotation = self._convert_annotation_dict(anno_object, int(image.image_id))
                    converted_annotations.append(annotation)

            converted_json["image"] = converted_image
            converted_json["annotations"] = converted_annotations

            # 3. pcd_images
            # logger.info(f"## idx is {idx}/{len(cuboid_filenames)}")
            image_filename_stem = Path(image_filename).stem
            filename_tokens = image_filename_stem.split('_')
            pcd_filename = Path(image_filename).stem + ".pcd"

            pcd_image_dict = dict()
            pcd_image_dict["id"] = int(image.image_id)
            pcd_image_dict["file_name"] = pcd_filename
            pcd_image_dict["license"] = 0

            converted_json["pcd_image"] = pcd_image_dict

            # 4. pcd_annotations
            # TODO: have to remove extra "00" from cuboid filenames
            cuboid_anno_filename = os.path.join(path_3d, "00" + filename_tokens[-1] + ".json")
            converted_json["pcd_annotations"] = []
            if cuboid_anno_filename in cuboid_filenames:
                cuboid_labels = utils.from_file(cuboid_anno_filename)
                converted_json["pcd_annotations"] = cuboid_labels

            # 5. write out the converted json to a file
            json_data = json.dumps(converted_json, default=utils.default, ensure_ascii=False, indent=2)

            output_folder = os.path.join(path_out, task_name)
            if not os.path.exists(output_folder):
                os.mkdir(output_folder)

            output_filename = os.path.join(output_folder, image_filename_stem + ".json")
            # logger.info(f"{output_filename}")
            utils.to_file(json_data, output_filename)
