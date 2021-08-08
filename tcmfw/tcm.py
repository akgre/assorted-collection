# -*- coding: utf-8 -*-
# The MIT License
#
# Copyright (c) 2018 Aaron Greenyer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
    tcm.py
    ~~~~~~~~~~~

    Test Control Manager to create an application that sets up and runs test scripts.

    :copyright: 2018 by Aaron Greenyer
    :license: MIT, see COPYING for more details.
"""

import os
import sys
import time
import win32api
import platform
import subprocess
from socket import gethostname  # gets network name of host PC running this script
from loguru import logger
import file_manager
import test_flow_control

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from configure_logger import setup_logging

module_name = "queue scripts"
__version__ = '0.1.0-dev1'

class TCMApp:
    def __init__(self, test_file_manager):
        self.setup_data = {}
        self.station_data = {}
        self.test_case_files = []
        self.test_file_manager = None
        self.script_ctrl = None
        self.test_module = None

        self.test_file_manager = test_file_manager
        self.init_test_script()

    def init_test_script(self):
        """
        Docs
        """
        self.setup_data['pyVersion'] = platform.python_version()  # Logging the Python Version
        self.setup_data['hostPC'] = gethostname()  # Logging the PC running the CTS scripts
        self.setup_data['user'] = win32api.GetUserName()
        self.setup_data['start_script_time'] = time.asctime()
        self.station_data.update(self.test_file_manager.station_data)
        self.setup_data.update(self.test_file_manager.setup_data)
        setup_logging(self.setup_data)
        self.test_case_files = self.test_file_manager.test_case_files

        logger.info('===========================================================')
        logger.info('                       TCM APPLICATION                     ')
        logger.info('===========================================================')


        logger.info(f'________________________________________________\n\n'
                    f'    Station ID : station_config.json\n'
                    f'________________________________________________\n')

        key_len = 0
        value_len = 0
        for key, value in self.station_data.items():
            key_len = (key_len, len(key))[len(key) > key_len] + 1
            value_len = (value_len, len(value))[len(value) > value_len]

        logger.info(f"____{'Station Key':<{key_len}}- {'Value':<{value_len}}")
        for key, value in self.station_data.items():
            logger.opt(ansi=True).info(
                f"    <yellow>{key:<{key_len}}</yellow>"
                f"- <cyan>{value:<{value_len}}</cyan>")

        logger.info(f'________________________________________________\n\n'
                    f'    Collecting Setup File Data: {self.setup_data["setup_file"]}\n'
                    f'________________________________________________\n')

        key_len = 0
        value_len = 0
        for key, value in self.setup_data.items():
            key_len = (key_len, len(key))[len(key) > key_len] + 1
            value_len = (value_len, len(value))[len(value) > value_len]

        logger.info(f"____{'Setup Key':<{key_len}}- {'Value':<{value_len}}")
        for key, value in self.setup_data.items():
            logger.opt(ansi=True).info(
                f"    <yellow>{key:<{key_len}}</yellow>"
                f"- <cyan>{value:<{value_len}}</cyan>")

        logger.info(f"\n____Test Cases List")
        for test_case_file in self.test_case_files:
            logger.opt(ansi=True).info(f'    <cyan>{test_case_file}</cyan>')

        self.script_ctrl = test_flow_control.FlowControl()

        sys.path.insert(0, os.path.normpath(f'{os.getcwd()}/test_modules/'))
        test_module_path = sys.path[0]
        test_file = self.setup_data.get('test_module', 'dummy_module')
        test_file = test_file + ('.py', '')['.py' in test_file]
        winVer = platform.release()

        if not os.path.isfile(f'{test_module_path}/{test_file}'):
            raise ModuleNotFoundError(f"    Test Module '{test_file}' not Found\n    "
                                      f"Check module name is correct or exists in the 'test_modules' folder")

        logger.info(f'________________________________________________\n\n'
                    f'    Loading Test Module: {test_file}\n'
                    f'________________________________________________\n')

        try:
            test_module_import = __import__(test_file.replace('.py', ''))
            setup_stuff = {'test_file': self.test_file_manager, 'script_ctrl': self.script_ctrl}
            self.test_module = test_module_import.load_test_object(setup_stuff)
        except Exception as e:
            logger.error('    Error loading module\n    {}'.format(e))
            self.script_ctrl.shutdown()
        logger.success(f"Success Loading: {test_file}")

    def check_setup_data(self):
        logger.info(f'________________________________________________\n\n'
                    f'    {self.test_module.check_setup_data_name}\n'
                    f'________________________________________________\n')
        if not self.test_module.check_setup_data(self.setup_data):
            logger.error('**** Setup File Check Failed. Unable to Start Test ****')
            return False
        logger.success('Setup File Check Success')
        return True

    def check_test_case_data(self):
        logger.info(f'________________________________________________\n\n'
                    f'    {self.test_module.check_definition_file_data_name}\n'
                    f'________________________________________________\n')
        if not self.test_case_files:
            self.test_case_files = self.test_module.generate_test_definitions()
            if not self.test_case_files:
                logger.error('**** No Test Case Data Available. Unable to Start Test ****')
                return False
            else:
                logger.info('Default definition file created')
        for test_definition_file in self.test_case_files:
            test_definitions = self.test_file_manager.test_definition_parser(test_definition_file)
            for test_data in test_definitions:
                if not self.test_module.check_test_definition(test_data):
                    logger.error('**** Test Case Data Check Failed. Unable to Start Test ****')
                    return False
        logger.success('Definition Files Check Success')
        return True

    def check_test_interface_bring_up(self):
        logger.info(f'________________________________________________\n\n'
                    f'    {self.test_module.interface_bring_up_name}\n'
                    f'________________________________________________\n')
        if not self.test_module.interface_bring_up():
            return False
        logger.success('Test Bring Up Success')
        return True

    def run_test_script(self):
        logger.info('\n========================================================='
                    '\n                  RUNNING TEST SCRIPT                    '
                    '\n=========================================================\n')

        test_file_index = 0
        if not self.test_case_files:
            logger.info(f'________________________________________________\n\n'
                        f'    {self.test_module.construct_test_name}\n'
                        f'________________________________________________\n')

            if not self.test_module.construct_test():
                logger.error('**** Test Case Construction Failed. Unable to Start Test ****')
                return False

            logger.success('Test Case Construction Success')

            logger.info(f'________________________________________________\n\n'
                        f'    {self.test_module.run_test_name}\n'
                        f'________________________________________________\n')

            if not self.test_module.run_test():
                logger.error('**** Test Run Failed ****')
                return False
            else:
                logger.info('Test Result Recorded')
            return True

        for test_file in self.test_case_files:
            self.test_file_manager.backup_test_case(test_file)
            test_file_index += 1
            list_of_test_definitions = self.test_file_manager.test_definition_parser(test_file)
            for test_definition_data in list_of_test_definitions:
                logger.info(f"\n------------------------------------------------\n\n"
                            f"    Running Test: {test_definition_data.get('test_name', '')}\n\n"
                            f"    Test ID: {test_definition_data.get('test_id', '')}"
                            f" ({int(list_of_test_definitions.index(test_definition_data)) + 1} of"
                            f" {len(list_of_test_definitions)})\n"
                            f"    From File: {test_file} ({test_file_index} of"
                            f" {len(self.test_case_files)})\n\n"
                            f"------------------------------------------------\n")

                logger.info(f'________________________________________________\n\n'
                            f'    Test Definition\n'
                            f'________________________________________________\n')

                key_len = 15
                value_len = 16
                for key, value in test_definition_data.items():
                    key_len = (key_len, len(key))[len(key) > key_len]+1
                    value_len = (value_len, len(value))[len(value) > value_len]

                logger.info(f"____{'Definition Key':<{key_len}}- {'Definition Value':<{value_len}}")
                for key, value in test_definition_data.items():
                    logger.opt(ansi=True).info(
                        f"    <magenta>{key:<{key_len}}</magenta>"
                        f"- <cyan>{value:<{value_len}}</cyan>")

                if not self.test_module.check_test_definition(test_definition_data):
                    logger.error('**** Test Case Data Check Failed. Unable to Start Test ****')
                    continue

                logger.info(f'________________________________________________\n\n'
                            f'    {self.test_module.construct_test_name}\n'
                            f'________________________________________________\n')

                if not self.test_module.construct_test(test_definition_data):
                    logger.error('**** Test Case Construction Failed. Unable to Start Test ****')
                    continue

                logger.success('Test Case Construction Success')

                search = True
                while search:
                    # logger.info(f'________________________________________________\n\n'
                    #             f'    {self.test_module.test_update_name}\n'
                    #             f'________________________________________________\n')
                    #
                    # if not self.test_module.test_update(test_definition_data):
                    #     return False
                    logger.info(f'________________________________________________\n\n'
                                f'    {self.test_module.run_test_name}\n'
                                f'________________________________________________\n')
                    if not self.test_module.run_test(test_definition_data):
                        logger.error('**** Test Run Failed ****')
                    else:
                        logger.info('Test Result Recorded')
                    search = False
                # record test result
        return True

    def wrap_up_test_script(self):
        self.test_module.wrap_up_test()
        if self.test_file_manager.has_no_results_file():
            logger.warning(f'')
            # logger.warning(f'No results have been collected: Delete results folder? (Y/N)')
            # rem_results_folder = input().upper()
            # if rem_results_folder == 'Y':
            #    logger.remove()
            #    self.test_file_manager.delete_results_folder()
        else:
            try:
                self.test_file_manager.backup_to_network()
            except Exception as ex:
                logger.exception(f'{ex}')
        try:
            self.test_file_manager.archive_test_results()
        except Exception as ex:
            logger.exception(f'{ex}')

    def tcm_app_main(self):
        for run_sequence in [self.check_setup_data, self.check_test_case_data, self.check_test_interface_bring_up]:
            if not run_sequence():
                self.script_ctrl.shutdown()
        logger.success(f"\n------------------------------------------------"
                       f"\n    Setup Complete: {self.setup_data.get('test_module', 'dummy_module')}.py"
                       f"\n------------------------------------------------")
        for run_sequence in [self.run_test_script, self.wrap_up_test_script]:
            if not run_sequence():
                self.script_ctrl.shutdown()


def main():
    """
    Docs
    """
    version_string = f"%(prog)s {__version__}\n" + \
                     f"Python:  {platform.python_version()}"

    parser = ArgumentParser(formatter_class=RawDescriptionHelpFormatter,
                            description=f"{module_name} (Version {__version__})"
                            )
    parser.add_argument("--version",
                        action="version", version=version_string,
                        help="Display version information and dependencies."
                        )
    parser.add_argument("--verbose", "-v", "-d", "--debug",
                        action="store_true", dest="verbose", default=False,
                        help="Display extra debugging information and metrics."
                        )
    parser.add_argument("--user", "-u",
                        action="store_true", dest="user", default=False,
                        help="Allows the user to edit the configurations."
                        )
    parser.add_argument("--setup", "-s",
                        action="store_true", dest="user", default=False,
                        help="Allows the user to edit the configurations."
                        )

    args = parser.parse_args()



    # formats the setup file include the file extension
    setup_file = dict(zip(['tcm.py', 'setup'], sys.argv)).get('setup', 'setup.csv')
    setup_file = setup_file + ('.csv', '')['.csv' in setup_file]
    try:
        test_file_manager = file_manager.TestFileManager(setup_file=setup_file)
    except FileNotFoundError:
        logger.error(f"ERROR: Setup File Not Found: {setup_file}")
    except OSError:
        logger.error("ERROR: Unable to create directory")
    except Exception as ex:
        logger.error(f'{ex}')
    else:
        try:
            test_app = TCMApp(test_file_manager)
            # start the stop/pause control gui
            if test_app.setup_data.get('app_control', '').upper() == 'Y':
                logger.debug(f"Starting GUI")
                sub_process_stop = subprocess.Popen('python StopMainFrame.py')
            test_app.tcm_app_main()
        except ModuleNotFoundError as ex:
            logger.error(f'{ex}')
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrupt")
        except Exception as ex:
            if 'test_stopped' in ex.args:
                pass
                # logger.warning("\nTest Stopped")
            else:
                logger.error("\nFailed During Run")
                logger.exception(f'{ex}')
    finally:
        try:
            logger.debug('end control GUI (subProcess_stop)')
            sub_process_stop.kill()
        except Exception as ex:
            logger.debug('subProcess_stop already closed')


if __name__ == "__main__":
    """
    Docs
    """
    main()
