import json
import math
import os

import attr

import src.common.utils as utils
from src.converters.base_reader import CONVERT_ID, CONVERT_VERSION
from src.models.adq_labels import AdqLabels
from src.common.logger import get_logger

logger = get_logger(__name__)


@attr.s(slots=True, frozen=False)
class DataLabels:
    twconverted = attr.ib(default=None, validator=attr.validators.instance_of(str))
    mode = attr.ib(default="annotation", validator=attr.validators.instance_of(str))
    template_version = attr.ib(default="0.1", validator=attr.validators.instance_of(str))
    images = attr.ib(default=[], validator=attr.validators.instance_of(list))
    meta_data = attr.ib(default=None)

    def to_json(self):
        return {
            "twconverted": self.twconverted,
            "mode": self.mode,
            "template_version": self.template_version,
            "images": self.images,
            "meta_data": self.meta_data
        }

    def save(self, filename: str):
        json_data = json.dumps(self.to_json(), default=utils.default, ensure_ascii=False, indent=2)
        utils.to_file(json_data, filename)

    def save_image(self, image_to_save: 'DataLabels.Image'):
        for idx, image in enumerate(self.images):
            if image.name == image_to_save.name:
                self.images[idx] = image_to_save
                break
        logger.error(f"Cannot find a matching image {image_to_save}")

    def get_class_labels(self):
        """
        :return: all class labels
        """
        class_labels = set()
        for image in self.images:
            image_class_labels = image.get_class_labels()
            class_labels = class_labels.union(image_class_labels)
        return class_labels

    def get_verification_result_sum(self):
        verification_result_sum = 0
        for image in self.images:
            for obj in image.objects:
                verification_result = obj.verification_result
                if verification_result:
                    verification_result_sum += 1
        return verification_result_sum

    @staticmethod
    def from_json(json_dict):
        return DataLabels(
            twconverted=json_dict['twconverted'],
            mode=json_dict['mode'],
            template_version=json_dict['template_version'],
            images=[DataLabels.Image.from_json(json_image) for json_image in json_dict['images']],
            meta_data=json_dict["meta_data"] if json_dict.get("meta_data") else None
        )

    @staticmethod
    def from_adq_labels(adq_labels: AdqLabels):
        return DataLabels(
            twconverted=adq_labels.twconverted,
            mode=adq_labels.mode,
            template_version=adq_labels.template_version,
            images=[DataLabels.Image.from_adq_image(image) for image in adq_labels.images],
            meta_data=adq_labels.meta_data
        )

    @staticmethod
    def from_image_filenames(image_filenames: list):
        """
        creates DataLabels object from image filenames with empty labels.
        :param image_filenames:
        :return:
        """
        images = []
        for idx, filename in enumerate(image_filenames):
            images.append(DataLabels.Image.from_filename(filename, image_id=str(idx)))

        return DataLabels(
            twconverted=CONVERT_ID,
            mode="annotation",
            template_version=CONVERT_VERSION,
            images=images
        )

    @staticmethod
    def load(filename: str) -> 'DataLabels':
        """
        :param filename: label filename
        :return: DartLabels object
        """
        json_labels = utils.from_file(filename)
        # check if it is already in DartLabels format
        # TODO: find a better way of checking the format
        if json_labels:
            if json_labels.get('images') and type(json_labels.get('images')[0]['height']) == int:
                return DataLabels.from_json(json_labels)
            else:
                adq_labels = AdqLabels.from_json(json_labels)
                # convert to dart label format for easier processing
                return DataLabels.from_adq_labels(adq_labels)
        else:
            logger.error("label file {} does not exist!".format(filename))

    @staticmethod
    def load_from_dict(label_files_dict: dict) -> dict:
        """
        :param label_files_dict: label files with key=folder value=label filename
        :return: a dictionary with key=label filename value=DartLabels
        """
        objects_dict = {}

        if label_files_dict and len(label_files_dict.items()) > 0:
            for folder, label_files in label_files_dict.items():
                for label_file in label_files:
                    objects_dict[label_file] = DataLabels.load(os.path.join(folder, label_file))

        return objects_dict

    @attr.s(slots=True, frozen=False)
    class Image:
        image_id = attr.ib(validator=attr.validators.instance_of(str))
        name = attr.ib(validator=attr.validators.instance_of(str))
        width = attr.ib(validator=attr.validators.instance_of(int))
        height = attr.ib(validator=attr.validators.instance_of(int))
        objects = attr.ib(default=[], validator=attr.validators.instance_of(list))

        # {
        #     "image_id": "0",
        #     "name": "WIN_20220913_14_01_16_Pro.jpg",
        #     "width": "3840",
        #     "height": "2160",
        #     "objects": [
        #
        # {
        #
        def to_json(self):
            return {
                "image_id": self.image_id,
                "name": self.name,
                "width": self.width,
                "height": self.height,
                "objects": self.objects
            }

        def get_class_labels(self):
            class_labels = set()
            for obj in self.objects:
                class_labels.add(obj.label)
            return class_labels

        def get_class_label_stats(self):
            class_labels = dict()
            for obj in self.objects:
                label = obj.label
                if class_labels.get(label):
                    class_labels[label] += 1
                else:
                    class_labels[label] = 1
            return class_labels

        @staticmethod
        def from_json(json_dict):
            return DataLabels.Image(
                image_id=json_dict['image_id'],
                name=json_dict['name'],
                width=json_dict['width'],
                height=json_dict['height'],
                objects=[DataLabels.Object.from_json(json_obj) for json_obj in json_dict['objects']]
            )

        @staticmethod
        def from_adq_image(adq_image: AdqLabels.Image):
            return DataLabels.Image(
                image_id=adq_image.image_id,
                name=adq_image.name,
                width=int(adq_image.width),
                height=int(adq_image.height),
                objects=[DataLabels.Object.from_adq_object(obj) for obj in adq_image.objects])

        @staticmethod
        def from_filename(filename, image_id='0'):
            width, height = utils.get_dimension(filename)
            return DataLabels.Image(
                image_id=image_id,
                name=os.path.basename(filename),
                width=width,
                height=height
            )

    @attr.s(slots=True, frozen=False)
    class Object:
        label = attr.ib(validator=attr.validators.instance_of(str))
        type = attr.ib(validator=attr.validators.instance_of(str))
        points = attr.ib(default=list)
        # a list of attribute_name and attribute_value pairs
        attributes = attr.ib(default=None)
        verification_result = attr.ib(default=None)

        # {
        #   "label": "4FM",
        #   "type": "box",
        #   "occluded": "0",
        #   "z_order": "7",
        #   "group_id": "",
        #   "position": "387.50000000, 195.90039062, 2034.10156250, 1256.60036621",
        #   "attributes": [],
        #   "verification_result": {
        #     "error_code": "DVE_RANGE",
        #     "comment": ""
        #   }
        # },
        # {
        #   "label": "UNTAG",
        #   "type": "box",
        #   "position": "1730, 1502, 1740, 1512",
        #   "occluded": "0",
        #   "z_order": "1",
        #   "verification_result": {
        #     "error_code": "DVE_UNTAG",
        #     "comment": ""
        #   }
        # }

        def to_json(self):
            return {
                "label": self.label,
                "type": self.type,
                "points": self.points,
                "attributes": self.attributes,
                "verification_result": self.verification_result,
            }

        @staticmethod
        def from_json(json_dict):
            return DataLabels.Object(label=json_dict['label'],
                                     type=json_dict['type'],
                                     points=json_dict.get('points', None),
                                     attributes=json_dict.get('attributes', None),
                                     verification_result=json_dict.get('verification_result', None)
                                     )

        @staticmethod
        def from_adq_object(adq_object: AdqLabels.Object):
            points_str = adq_object.position.split()
            points = [[float(point.replace(",", "")) for point in points_str]]

            attributes = dict()
            attributes['occluded'] = int(adq_object.occluded) if adq_object.group_id else 0
            attributes['z_order'] = int(adq_object.z_order) if adq_object.group_id else 0
            attributes['group_id'] = int(adq_object.group_id) if adq_object.group_id else 0

            for attribute in adq_object.attributes:
                key = attribute["attribute_name"]
                value = attribute["attribute_value"]
                attributes[key] = value

            return DataLabels.Object(label=adq_object.label,
                                     type=adq_object.type,
                                     points=points,
                                     attributes=attributes,
                                     verification_result=adq_object.verification_result)

        @staticmethod
        def get_bounding_rectangle(label_object) -> list:
            """
            get the rectangle of a polygon or a spline
            :param label_object: label object whose points could be [[x,y,r]...] or [[x,y]...]
            :return: xtl,ytl, xbr,ybr
            """
            if label_object.type == 'box':
                return label_object.points[0]

            x_index, y_index = 0, 1
            points = label_object.points

            if points:
                min_x, max_x = math.inf, -math.inf
                min_y, max_y = math.inf, -math.inf

                # Iterate over the remaining control points and update the minimum and maximum x and y values
                for pt in points:
                    x = int(pt[x_index])
                    y = int(pt[y_index])
                    if x < min_x:
                        min_x = x
                    if x > max_x:
                        max_x = x

                    if y < min_y:
                        min_y = y
                    if y > max_y:
                        max_y = y

                return [min_x, min_y, max_x, max_y]
