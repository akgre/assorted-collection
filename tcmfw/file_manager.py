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
    file_manager.py
    ~~~~~~~~~~~

    Test File Manager

    This module manages the file organisation for a test

    Features:

    setup_parser::
    Collects the parameters from the setup file which controls the test setup.

    create_test_dir::

    create_script_backup::

    :copyright: 2018 by Aaron Greenyer
    :license: MIT, see COPYING for more details.
"""

import os
import csv
import json
import shutil
import datetime
from pathlib import Path


class TestFileManager:
    """
    Docs
    """

    def __init__(self, setup_file='setup.csv'):
        """
        Docs
        """
        self.file_manager_config = {}
        self.setup_data = self.setup_parser(setup_file)
        self.station_data = self.station_parser()
        self.test_case_files = self.test_case_files_parser(setup_file)
        self.create_test_dir()
        self.create_script_backup()
        self.results_dir = self.file_manager_config['results_dir']

    def station_parser(self, station_file='station_config.json', file_dir='..\\'):
        station_file_path = Path(station_file)
        if not station_file_path.exists():
            station_file_path = (Path.cwd() / file_dir / station_file).resolve()
            if not station_file_path.exists():
                return False

        with open(station_file_path) as f:
            station_cf_data = json.load(f)

        return station_cf_data


    def setup_parser(self, setup_file='setup.csv', file_dir='..\\setup_files'):
        """
        Docs
        """
        setup_file_path = Path(setup_file)
        if not setup_file_path.exists():
            setup_file_path = (Path.cwd() / file_dir / setup_file).resolve()
            if not setup_file_path.exists():
                return False

        self.file_manager_config['setup_file'] = setup_file_path

        setup_data_dict = {'setup_file': setup_file_path.name}
        with open(setup_file_path, mode='r') as read_setup_file:
            setup_reader = csv.reader(read_setup_file, delimiter=',')
            for setup_row in setup_reader:
                if len(setup_row) > 0:
                    if setup_row[0].strip() == 'test_case_files':
                        break
                    if setup_row[0].strip() != '':
                        if len(setup_row) > 1:
                            setup_data_dict[setup_row[0].lower()] = setup_row[1]
                        else:
                            setup_data_dict[setup_row[0].lower()] = ''
        setup_data_dict['setup_file_path'] = str(setup_file_path)
        return setup_data_dict

    def test_case_files_parser(self, setup_file='setup.csv', file_dir='..\\setup_files'):
        """
        Docs
        """
        setup_file_path = Path(setup_file)
        if not setup_file_path.exists():
            setup_file_path = (Path.cwd() / file_dir / setup_file).resolve()
            if not setup_file_path.exists():
                return False

        test_case_files = []
        listing_test_cases = False
        with open(setup_file_path, mode='r') as read_setup_file:
            setup_reader = csv.reader(read_setup_file, delimiter=',')
            for setup_row in setup_reader:
                if len(setup_row) > 0:
                    if setup_row[0].strip() == 'test_case_files':
                        listing_test_cases = True
                    if listing_test_cases:
                        if setup_row[0].strip().upper() == 'Y':
                            if len(setup_row) > 1:
                                test_case_files.append(setup_row[1])
        self.file_manager_config['test_cases_dir'] = str((Path.cwd() / "..\\test_cases").resolve())

        return test_case_files

    def test_definition_parser(self, test_case_file='', file_dir='..\\test_cases'):
        """
        Docs
        """
        test_case_file = Path(test_case_file)
        if not test_case_file.exists():
            test_case_file = (Path.cwd() / file_dir / test_case_file).resolve()
            if not test_case_file.exists():
                print(f'file not found: {test_case_file}')
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

        return test_definitions

    def create_test_dir(self):
        """
        Docs
        """
        self.file_manager_config['test_title'] = f"{self.setup_data.get('title', 'test run')}"
        self.file_manager_config['date_time'] = datetime.datetime.now().strftime("%y-%m-%d_%H-%M")
        self.file_manager_config['results_dir'] = str(Path("..\\results\\",
                                                           f"{self.file_manager_config['date_time']}"
                                                           f"_{self.file_manager_config['test_title']}").resolve())

        if Path(self.file_manager_config['results_dir']).exists():
            self.file_manager_config['date_time'] = datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S")
            self.file_manager_config['results_dir'] = str(Path("..\\results\\",
                                                               f"{self.file_manager_config['date_time']}"
                                                               f"_{self.file_manager_config['test_title']}").resolve())

        self.file_manager_config['test_logs_dir'] = str(Path(f"{self.file_manager_config['results_dir']}",
                                                             "logs").resolve())
        # self.file_manager_config['all_iteration_results_dir'] = \
        #    f"{self.file_manager_config['results_dir']}\\all_iteration_results"
        Path(self.file_manager_config['results_dir']).mkdir(parents=True)
        Path(self.file_manager_config['test_logs_dir']).mkdir(parents=True)
        # os.mkdir(self.file_manager_config['all_iteration_results_dir'])
        self.file_manager_config['no_results_file'] = str(Path(f"{self.file_manager_config['results_dir']}",
                                                               "no_results_recorded.txt").resolve())
        with open(self.file_manager_config['no_results_file'], "w") as no_res_file:
            no_res_file.write("There are no results in this directory so this \
                                     file can probably be deleted.")
        self.setup_data['date_time'] = self.file_manager_config['date_time']
        self.setup_data['results_dir'] = self.file_manager_config['results_dir']
        self.setup_data['test_logs_dir'] = self.file_manager_config['test_logs_dir']

    def create_script_backup(self):
        """
        Docs
        """
        shutil.copytree(Path.cwd(), f"{self.file_manager_config['results_dir']}\\test_scripts_backup\\tcmfw")

        shutil.copy2(self.file_manager_config['setup_file'],
                     f"{self.file_manager_config['results_dir']}\\test_scripts_backup\\")

        setup_file_backup_path = Path(f"{self.file_manager_config['results_dir']}", "test_scripts_backup",
                                      f"{Path(self.file_manager_config['setup_file']).name}").resolve()

        setup_file_backup_path.rename(Path(f"{self.file_manager_config['results_dir']}", "test_scripts_backup",
                                           f"{self.file_manager_config['date_time']}"
                                           f"_{setup_file_backup_path.name}").resolve())

        self.file_manager_config['test_cases_backup_dir'] = str(Path(f"{self.file_manager_config['results_dir']}",
                                                                     "test_scripts_backup",
                                                                     "test_cases").resolve())
        Path(self.file_manager_config['test_cases_backup_dir']).mkdir(parents=True)

        if self.setup_data.get('pathloss_file', '') != '':
            path_loss_file = Path("..\\test_cases", "pathloss_files",
                                  f"{self.setup_data.get('pathloss_file', 'default_pathloss_file.csv')}").resolve()
            if path_loss_file.exists():
                shutil.copy2(str(path_loss_file), f"{self.file_manager_config['results_dir']}\\test_scripts_backup\\")
            else:
                print(f'Unable to copy: {str(path_loss_file)}')

    def backup_test_case(self, test_case_file='', file_dir='..\\test_cases'):
        """
        Docs
        """
        if not os.path.exists(test_case_file):
            test_case_file = os.path.abspath(f'{file_dir}\\{test_case_file}')
        if os.path.isfile(test_case_file):
            if not os.path.isfile(f"{self.file_manager_config['test_cases_backup_dir']}\\{test_case_file}"):
                shutil.copy2(test_case_file, self.file_manager_config['test_cases_backup_dir'])

    def append_to_history_log(self):
        """
        Docs
        """
        if not os.path.isfile(os.path.abspath('..\\results\\test_history_log.csv')):
            # create file if not found.
            with open(os.path.abspath('..\\results\\test_history_log.csv'), 'w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow('Date/Time, Setup File, Test Description, Input Files')
        self.file_manager_config['test_history_log'] = os.path.abspath('..\\results\\test_history_log.csv')

    def has_no_results_file(self):
        if os.path.isfile(self.file_manager_config['no_results_file']):
            return True
        return False

    def delete_results_folder(self):
        shutil.rmtree(self.results_dir)

    def test_description(self, file_name, file_info):
        """
        Docs
        """
        abs_file_path = os.path.join(self.results_dir, file_name)
        with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(file_info)

    def add_iteration_result_header(self, file_name, header):
        """
        Docs
        """
        abs_file_path = os.path.join(self.file_manager_config['all_iteration_results_dir'], file_name)
        with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header)

    def save_iteration_result(self, file_name, results):
        """
        Docs
        """
        if os.path.isfile(self.file_manager_config['no_results_file']):
            os.remove(self.file_manager_config['no_results_file'])
        abs_file_path = os.path.join(self.file_manager_config['all_iteration_results_dir'], file_name)
        with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(results)

    def add_final_result_header(self, file_name, header):
        """
        Docs
        """
        abs_file_path = os.path.join(self.results_dir, file_name)
        with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header)

    def save_final_result(self, file_name, results):
        """
        Docs
        """
        writer_header = False
        if os.path.isfile(self.file_manager_config['no_results_file']):
            os.remove(self.file_manager_config['no_results_file'])
        abs_file_path = os.path.join(self.results_dir, file_name)
        if not os.path.isfile(abs_file_path + '.csv'):
            writer_header = True
        if type(results) == list:
            with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(results)
        elif type(results) == dict:
            try:
                fieldnames = list(results.keys())
                with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if writer_header:
                        writer.writeheader()
                    writer.writerow(results)
            except IOError as errno:
                print('Write dict error: ' + errno)
        return

    def check_results_file_exists(self, file_name):
        return os.path.isfile(os.path.normpath(f'{self.results_dir}/{file_name}.csv'))

    def backup_to_network(self):
        if self.setup_data.get('network_directory', '') != '':
            network_dir = f"{self.setup_data.get('network_directory', '')}" \
                f"\\{self.setup_data['platform_serial']}" \
                f"\\{self.setup_data['board_serial']}" \
                f"\\{self.setup_data['software_version']}" \
                f"\\{os.path.basename(self.setup_data['results_dir'])}"
            if len(network_dir) > 255:
                print('File Name Too Long')
            else:
                shutil.copytree(self.setup_data['results_dir'], network_dir)

    def archive_test_results(self):
        try:
            if len(f"T:\\agreenyer\\TCM_test_results\\results_archive\\{os.path.basename(self.setup_data['results_dir'])}") > 255:
                print('File Name Too Long')
            else:
                shutil.copytree(self.file_manager_config['results_dir'], f"T:\\agreenyer\\TCM_test_results\\"
                f"results_archive\\{os.path.basename(self.setup_data['results_dir'])}")
        except Exception as ex:
            print(ex)

    def create_test_definition_file(self, file_name, definition_list):
        abs_file_path = os.path.join(self.file_manager_config['test_cases_dir'], file_name)
        if not definition_list:
            raise Exception("Error - No Folders in the Source Folder")
        try:
            with open(abs_file_path, 'w', newline='') as definition_file:
                writer = csv.DictWriter(definition_file, definition_list[0].keys())
                writer.writeheader()
                writer.writerow({'run': 'START'})
                for dict_data in definition_list:
                    writer.writerow(dict_data)
                writer.writerow({'run': 'END'})
        except IOError as errno:
            print('bob ' + errno)
        return
