import os

import pandas as pd

from src.common.logger import get_logger
from .base_reader import BaseReader

logger = get_logger(__name__)


class Project85CsvReader(BaseReader):
    def __init__(self):
        super().__init__()
        self.columns = None

    def parse(self, csv_files, data_files=None):
        super().parse(csv_files, data_files)

        metadata_dict = dict()

        for csv_file in csv_files:
            df = pd.read_csv(csv_file, names=self.columns)
            # logger.info(df)

            if len(df) > 1:
                df = df.drop(0, axis=0).reset_index(drop=True)

            csv_filename = os.path.basename(csv_file)

            # Convert DataFrame to a dictionary with single values, not nested
            df_dict = df.squeeze().to_dict()

            # Remove the index key (0) from the dictionary
            df_dict = {k: v for k, v in df_dict.items() if k != 0}
            # Add a new dictionary entry with the filename as the key
            metadata_dict[csv_filename] = df_dict

        return metadata_dict
