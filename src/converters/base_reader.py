from abc import ABC

CONVERT_ID = "96E7D8C8-44E4-4055-8487-85B3208E51A2"
CONVERT_VERSION = "0.1"


class BaseReader(ABC):
    def __init__(self):
        self.data_labels_dict = {}

    def parse(self, label_files: list, data_files: list = None) -> dict:
        self.data_labels_dict['mode'] = 'annotation'
        self.data_labels_dict['twconverted'] = CONVERT_ID
        self.data_labels_dict['template_version'] = CONVERT_VERSION
        return self.data_labels_dict
