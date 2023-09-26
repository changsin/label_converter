import xml.etree.ElementTree as ET
import src.common.utils as utils

from .base_reader import BaseReader

BO_SHAPE_TYPES = ['box', 'polygon', 'polyline', 'points', 'face', 'body', 'leftHand', 'rightHand']


class CVATReader(BaseReader):

    def _parse_element(self, element):
        if len(element) == 0:
            return element.text
        result = {}
        for child in element:
            child_data = self._parse_element(child)
            if child.tag in result:
                if type(result[child.tag]) is list:
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = [result[child.tag], child_data]
            else:
                result[child.tag] = child_data
        return result

    def parse(self, label_files, data_files=None):
        super().parse(label_files, data_files)

        for label_file in label_files:
            xml_structure = ET.parse(label_file)

            root_info = xml_structure.getroot()
            if root_info.tag != 'annotations':
                raise Exception(label_file + 'is not a supported CVAT format.')

            el_meta_data = root_info.find('meta')
            if el_meta_data:
                meta_data_dict = self._parse_element(el_meta_data)
                self.data_labels_dict['meta_data'] = meta_data_dict

            project_name = utils.get_dict_value(self.data_labels_dict['meta_data'], "task/name")

            images = list()
            el_images = root_info.findall('image')
            for el_image in el_images:
                image_dict = dict()
                image_dict['image_id'] = el_image.attrib['id']
                image_dict['name'] = el_image.attrib['name']
                image_dict['width'] = el_image.attrib['width']
                image_dict['height'] = el_image.attrib['height']

                objects_list = list()
                for object_type in BO_SHAPE_TYPES:
                    el_objects = el_image.findall(object_type)
                    for el_object in el_objects:
                        object_dict = dict()
                        object_dict['label'] = el_object.attrib['label']
                        object_dict['type'] = object_type

                        try:
                            object_dict['occluded'] = el_object.attrib['occluded']
                        except KeyError:
                            object_dict['occluded'] = "0"

                        try:
                            object_dict['z_order'] = el_object.attrib['z_order']
                        except KeyError:
                            object_dict['z_order'] = "0"

                        try:
                            object_dict['group_id'] = el_object.attrib['group_id']
                        except KeyError:
                            object_dict['group_id'] = ""

                        if object_type == 'box':
                            object_dict['position'] = "{}, {}, {}, {}".format(el_object.attrib['xtl'],
                                                                              el_object.attrib['ytl'],
                                                                              el_object.attrib['xbr'],
                                                                              el_object.attrib['ybr'])
                        else:
                            object_dict['position'] = el_object.attrib['points']

                        attributes = list()
                        el_attributes = el_object.findall('attribute')
                        for each_attr in el_attributes:
                            attributes_dict = dict()
                            attributes_dict['attribute_name'] = each_attr.attrib['name']
                            attributes_dict['attribute_value'] = each_attr.text
                            attributes.append(attributes_dict)

                        object_dict['attributes'] = attributes
                        objects_list.append(object_dict)

                image_dict['objects'] = objects_list
                images.append(image_dict)

            self.data_labels_dict['images'] = images
        return self.data_labels_dict
