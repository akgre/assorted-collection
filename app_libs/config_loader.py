#!/usr/bin/env python3

import os
import json
import time
import platform
import getpass
import datetime

from socket import gethostname  # gets network name of host PC running this script
from os.path import join, isfile, expanduser, getmtime, basename, isdir, isfile, dirname
from loguru import logger

DEFAULT_CONFIG_FILE_DIR = ''
DEFAULT_CONFIG_FILE = ''

class _Config:
    def __init__(self):
        self.config_file_name = ''
        self.config_file_path = ''
        self._update_history = []
        self._configDict = {}

    def __getattr__(self, name):
        try:
            return self._configDict[name]
        except KeyError:
            return getattr(self._configDict, name)

    def _getConfigFile(self):
        """@brief Get the config file."""
        fp = open(self.config_file_path, 'r')
        self._configDict = json.load(fp)
        fp.close()

    def load_config(self, config_file_path=None):

        if config_file_path is None:
            raise Exception("No config file selected")

        if not isdir(dirname(config_file_path)):
            raise Exception(f"config directory not found: {config_file_path}")

        if not isfile(config_file_path):
            raise Exception(f"config directory not found: {config_file_path}")

        self.config_file_path = config_file_path
        self._getConfigFile()

        self._configDict['CONFIG_FILE'] = config_file_path
        self._configDict['PYTHON_VERSION'] = platform.python_version()
        self._configDict['HOST_PC'] = gethostname()
        self._configDict['USER_NAME'] = getpass.getuser()
        self._configDict['START_SCRIPT_TIME'] = time.asctime()
        self._configDict['DATE_TIME'] = datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S")

    def getConfigDict(self):
        """@return the dict holding the configuration."""
        return self._configDict

    def updateConfigValue(self, configKey, configValue):
        """@return the dict holding the configuration."""
        self._update_history.append((configKey, self._configDict[configKey]))
        self._configDict.update({configKey: configValue})

    def updateConfigValue(self, configKey, configValue):
        """@return the dict holding the configuration."""
        self._update_history.append((configKey, self._configDict[configKey]))
        self._configDict.update({configKey: configValue})

    def show(self):
        """@brief Show the state of configuration parameters.
           @param uio The UIO instance to use to show the parameters."""
        key_len = 0
        value_len = 0
        for key, value in self.getConfigDict().items():
            key_len = (key_len, len(key))[len(key) > key_len] + 1
            value_len = (value_len, len(value))[len(value) > value_len]

        logger.info(f"____Config File: {self.config_file_path}")
        logger.info(f"    {'Key':<{key_len}}- {'Value':<{value_len}}")
        for key, value in self.getConfigDict().items():
            logger.opt(ansi=True).info(
                f"    <yellow>{key:<{key_len}}</yellow>"
                f"- <cyan>{value:<{value_len}}</cyan>")

        if self._update_history:
            logger.debug(f"____Config Updated Values:")
            logger.debug(f"    {'Key':<{key_len}}- {'Previous Value':<{value_len}}")
            for key, value in self._update_history:
                logger.opt(ansi=True).debug(
                    f"    <yellow>{key:<{key_len}}</yellow>"
                    f"- <cyan>{value:<{value_len}}</cyan>")
        else:
            logger.debug(f"config not modified: {self._update_history}")

config = _Config()
