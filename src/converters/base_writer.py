from abc import ABC


class BaseWriter(ABC):
    def __init__(self):
        self.data_labels_dict = {}

    def write(self, file_in: str, file_out: str) -> None:
        pass
