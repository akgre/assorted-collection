#!/usr/bin/env python3

import shutil
import csv

from pathlib import Path
from loguru import logger

class DataController(object):

    def __init__(self):
        self._configDict = {}
        self._dataIndexRefDict = {}
        self._testDefinitions = {}

    def __getattr__(self, name):
        try:
            return self._dataIndexRefDict[name]
        except KeyError:
            return getattr(self._dataIndexRefDict, name)

    def getIndexReferenceDict(self):
        """@return the dict holding the configuration."""
        return self._dataIndexRefDict

    def build(self, config_dict):
        self._configDict = config_dict

        CONFIG_FILE = self._configDict['CONFIG_FILE']
        TEST_CASE_FILE_PATH = self._configDict['TEST_CASE_FILE_PATH']
        LOG_PATH_COPY = self._configDict['LOG_PATH_COPY']
        RESULTS_PATH = self._configDict['RESULTS_PATH']
        TITLE = self._configDict['TITLE']
        DATE_TIME = self._configDict['DATE_TIME']

        RESULTS_BASE_DIR = str(Path(RESULTS_PATH, f'{DATE_TIME[:-3]}_{TITLE}').resolve())

        if Path(RESULTS_BASE_DIR).exists():
            RESULTS_BASE_DIR = str(Path(RESULTS_PATH, f'{DATE_TIME}_{TITLE}').resolve())

        RESULTS_LOG_DIR = str(Path(RESULTS_BASE_DIR, 'logs').resolve())
        LOG_PATH_COPY_DIR = str(Path(LOG_PATH_COPY).resolve())
        NO_RESULTS_FILE = str(Path(RESULTS_BASE_DIR, "no_results_recorded.txt").resolve())

        self._dataIndexRefDict['CONFIG_FILE'] = CONFIG_FILE
        self._dataIndexRefDict['TEST_CASE_FILE_PATH'] = TEST_CASE_FILE_PATH
        self._dataIndexRefDict['RESULTS_BASE_DIR'] = RESULTS_BASE_DIR
        self._dataIndexRefDict['RESULTS_LOG_DIR'] = RESULTS_LOG_DIR
        self._dataIndexRefDict['LOG_PATH_COPY_DIR'] = LOG_PATH_COPY_DIR
        self._dataIndexRefDict['NO_RESULTS_FILE'] = NO_RESULTS_FILE

        Path(RESULTS_BASE_DIR).mkdir(parents=True)
        Path(RESULTS_LOG_DIR).mkdir(parents=True)
        if not Path(LOG_PATH_COPY_DIR).exists():
            Path(LOG_PATH_COPY_DIR).mkdir(parents=True)
        with open(NO_RESULTS_FILE, "w") as no_res_file:
            no_res_file.write("There are no results in this directory so this file can probably be deleted.")

        self.run_time_copy()

    def run_time_copy(self):

        CONFIG_FILE = self._dataIndexRefDict['CONFIG_FILE']
        TEST_CASE_FILE_PATH = self._dataIndexRefDict['TEST_CASE_FILE_PATH']
        RESULTS_BASE_DIR = self._dataIndexRefDict['RESULTS_BASE_DIR']

        RUN_TIME_FILES = str(Path(RESULTS_BASE_DIR, 'run_time_files').resolve())

        Path(RUN_TIME_FILES).mkdir(parents=True)

        shutil.copy2(CONFIG_FILE, RUN_TIME_FILES)
        shutil.copy2(TEST_CASE_FILE_PATH, RUN_TIME_FILES)

    def show(self):
        key_len = 0
        value_len = 0
        for key, value in self.getIndexReferenceDict().items():
            key_len = (key_len, len(key))[len(key) > key_len] + 1
            value_len = (value_len, len(value))[len(value) > value_len]

        logger.debug("____Data Controller Index Reference")
        logger.debug(f"    {'Key':<{key_len}}- {'Value':<{value_len}}")
        for key, value in self.getIndexReferenceDict().items():
            logger.opt(ansi=True).debug(
                f"    <yellow>{key:<{key_len}}</yellow>"
                f"- <cyan>{value:<{value_len}}</cyan>")

    def getTestDefinitions(self):
        """@return the dict holding the configuration."""
        return self._testDefinitions

    def load_test_definitions(self):
        """
        Docs
        """
        test_case_file = Path(self._dataIndexRefDict['TEST_CASE_FILE_PATH']).resolve()

        if not test_case_file.exists():
            logger.error(f'file not found: {test_case_file}')
            return False

        test_definitions = []
        with open(test_case_file, mode='r') as read_test_case_file:
            definitions_reader = csv.DictReader(read_test_case_file, delimiter=',')

            append_to_definitions = False
            for row in definitions_reader:
                if row.get("run", '').upper() == 'START':
                    append_to_definitions = True
                elif row.get("run", '').upper() == 'END':
                    append_to_definitions = False

                if append_to_definitions:
                    if '' in row.keys():
                        del row['']
                    if row.get("run", '').upper() == 'Y':
                        del_list = []
                        for key, value in row.items():
                            if value == '':
                                del_list.append(key)
                        for item in del_list:
                            del row[item]
                        test_definitions.append(row)

        self._testDefinitions = test_definitions

    def show_test_definition(self, test_definition):
        key_len = 0
        value_len = 0
        for key, value in test_definition.items():
            key_len = (key_len, len(key))[len(key) > key_len] + 1
            value_len = (value_len, len(value))[len(value) > value_len]

        logger.info(f"____Definition File: {Path(self._dataIndexRefDict['TEST_CASE_FILE_PATH']).name}")
        logger.info(f"    {'Key':<{key_len}}- {'Value':<{value_len}}")
        for key, value in test_definition.items():
            logger.opt(ansi=True).info(
                f"    <yellow>{key:<{key_len}}</yellow>"
                f"- <cyan>{value:<{value_len}}</cyan>")

data_controller = DataController()

