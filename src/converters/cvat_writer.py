import datetime
import xml.dom.minidom
import xml.etree.ElementTree as ET

from src.common.logger import get_logger
from src.models.data_labels import DataLabels
from .base_writer import BaseWriter

SHAPE_TYPES = ['KEYPOINTS', 'POLYGON']

logger = get_logger(__name__)


CVAT_VERSION = "1.1"


class CVATWriter(BaseWriter):
    def write(self, file_in: str, file_out: str) -> None:
        data_labels = DataLabels.load(file_in)

        # Create the root element
        el_root = ET.Element("annotations")

        # Create child elements and add them to the root
        el_version = ET.SubElement(el_root, "version")
        el_version.text = CVAT_VERSION

        el_meta = ET.SubElement(el_root, "meta")
        el_task = ET.SubElement(el_meta, "task")
        el_mode = ET.SubElement(el_task, "mode")
        el_mode.text = "annotation"
        el_created = ET.SubElement(el_task, "created")
        el_created.text = str(datetime.datetime.now())
        el_updated = ET.SubElement(el_task, "updated")
        el_updated.text = str(datetime.datetime.now())

        labels_color = dict()

        # el_labels = ET.SubElement(el_root, "labels")
        for image in data_labels.images:
            el_image = ET.SubElement(el_root, "image")
            el_image.attrib["id"] = image.image_id
            el_image.attrib["name"] = image.name
            el_image.attrib["width"] = str(image.width)
            el_image.attrib["height"] = str(image.height)

            for idx, obj in enumerate(image.objects):
                if obj.type == "polygon" or obj.type == "segmentation":
                    el_obj = ET.SubElement(el_image, "polygon")
                    el_obj.attrib["label"] = obj.label
                    el_obj.attrib["occluded"] = "0"
                    el_obj.attrib["source"] = "manual"
                    el_obj.attrib["z_order"] = "0"
                    # Using list comprehension to convert each point array to a string
                    points_str = ";".join([f"{point[0]},{point[1]}" for point in obj.points])
                    el_obj.attrib["points"] = points_str

                    el_attrib_class_name = ET.SubElement(el_obj, "attribute")
                    el_attrib_class_name.attrib["name"] = "class_name"
                    el_attrib_class_name.text = obj.label

                    el_attrib_instance_id = ET.SubElement(el_obj, "attribute")
                    el_attrib_instance_id.attrib["name"] = "instance_id"
                    el_attrib_instance_id.text = str(idx)

                    attributes = obj.attributes
                    if attributes:
                        for attribute in attributes:
                            if not labels_color.get(obj.label):
                                if attribute["attribute_name"] == "color":
                                    rgba_value = attribute["attribute_value"]
                                    # Convert the RGBA values to a hexadecimal color
                                    hex_color = "#{:02X}{:02X}{:02X}".format(rgba_value["r"],
                                                                             rgba_value["g"],
                                                                             rgba_value["b"])
                                    labels_color[obj.label] = hex_color

        if labels_color.items():
            el_labels = ET.SubElement(el_task, "labels")
            for label, hex_color in labels_color.items():
                el_label = ET.SubElement(el_labels, "label")
                el_name = ET.SubElement(el_label, "name")
                el_name.text = label
                el_color = ET.SubElement(el_label, "color")
                el_color.text = hex_color
                el_values = ET.SubElement(el_label, "values")
                el_values.text = label

        # Use minidom to pretty-print the XML
        xml_str = ET.tostring(el_root, encoding="utf-8", method="xml")
        dom = xml.dom.minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")

        # Write the pretty-printed XML to the file
        with open(file_out, "wb") as f:  # Open the file in binary write mode
            f.write(pretty_xml.encode("utf-8"))


