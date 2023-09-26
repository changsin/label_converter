import os

import pandas as pd

from src.common.logger import get_logger
from .base_reader import BaseReader

logger = get_logger(__name__)

MD_COLUMNS1 = ["site", "location", "date", "address", "floor", "door", "wall"]
MD_COLUMNS2 = ["weather", "temperature", "lumen", "decibel"]
MD_COLUMNS3 = ["robot_id", "scenario_id", "pilot_id", "driving_type"]
MD_COLUMNS4 = ["scenario_start_time", "scenario_end_time", "distance_traveled", "driving_time"]
MD_COLUMNS5 = ["raw_data_filename"]
METADATA_COLUMN_NAMES = MD_COLUMNS1 + MD_COLUMNS2 + MD_COLUMNS3 + MD_COLUMNS4 + MD_COLUMNS5


class Project85CsvReader(BaseReader):
    def parse(self, csv_files, data_files=None):
        super().parse(csv_files, data_files)

        metadata_dict = dict()

        for csv_file in csv_files:
            df = pd.read_csv(csv_file, names=METADATA_COLUMN_NAMES)
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
