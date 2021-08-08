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
import shutil
import datetime


class TestFileManager:
    '''
    Docs
    '''
    def __init__(self, setup_file='setup.csv'):
        '''
        Docs
        '''
        self.file_manager_config = {}
        self.setup_data = self.setup_parser(setup_file)
        self.test_case_files = self.test_case_files_parser(setup_file)
        self.create_test_dir()
        self.create_script_backup()
        self.results_dir = self.file_manager_config['results_dir']

    def setup_parser(self, setup_file='setup.csv', file_dir='..\\setup_files'):
        '''
        Docs
        '''
        if not os.path.isabs(setup_file):
            setup_file = os.path.abspath(f'{file_dir}\\{setup_file}')
        self.file_manager_config['setup_file'] = setup_file

        setup_data = {'setup_file': os.path.basename(setup_file)}
        with open(setup_file, mode='r') as read_setup_file:
            setup_reader = csv.reader(read_setup_file, delimiter=',')
            for setup_row in setup_reader:
                if len(setup_row) > 0:
                    if setup_row[0].strip() == 'test_case_files':
                        break
                    if setup_row[0].strip() != '':
                        if len(setup_row) > 1:
                            setup_data[setup_row[0].lower()] = setup_row[1]
                        else:
                            setup_data[setup_row[0].lower()] = ''
        setup_data['setup_file_path'] = setup_file
        return setup_data

    def test_case_files_parser(self, setup_file='setup.csv', file_dir='..\\setup_files'):
        '''
        Docs
        '''
        if not os.path.isabs(setup_file):
            setup_file = os.path.abspath(f'{file_dir}\\{setup_file}')

        test_case_files = []
        listing_test_cases = False
        with open(setup_file, mode='r') as read_setup_file:
            setup_reader = csv.reader(read_setup_file, delimiter=',')
            for setup_row in setup_reader:
                if len(setup_row) > 0:
                    if setup_row[0].strip() == 'test_case_files':
                        listing_test_cases = True
                    if listing_test_cases:
                        if setup_row[0].strip().upper() == 'Y':
                            if len(setup_row) > 1:
                                test_case_files.append(setup_row[1])
        self.file_manager_config['test_cases_dir'] = os.path.abspath(f"..\\test_cases")
        return test_case_files

    def test_definition_parser(self, test_case_file='', file_dir='..\\test_cases'):
        '''
        Docs
        '''
        if not os.path.isabs(test_case_file):
            test_case_file = os.path.abspath(f'{file_dir}\\{test_case_file}')
        if not os.path.isfile(test_case_file):
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
                        for key, value in row.items():
                            if value == '':
                                del row[key]
                        test_definitions.append(row)

        return test_definitions

    def create_test_dir(self):
        '''
        Docs
        '''
        self.file_manager_config['test_title'] = f"{self.setup_data.get('title', 'test run')}"
        self.file_manager_config['date_time'] = datetime.datetime.now().strftime("%y-%m-%d_%H-%M")
        self.file_manager_config['results_dir'] = os.path.abspath(f"..\\results\\"
                                                                  f"{self.file_manager_config['date_time']}"
                                                                  f"_{self.file_manager_config['test_title']}")
        if os.path.exists(self.file_manager_config['results_dir']):
            self.file_manager_config['date_time'] = datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S")
            self.file_manager_config['results_dir'] = os.path.abspath(f"..\\results\\"
                                                                      f"{self.file_manager_config['date_time']}"
                                                                      f"_{self.file_manager_config['test_title']}")
        self.file_manager_config['test_logs_dir'] = f"{self.file_manager_config['results_dir']}\\logs"
        # self.file_manager_config['all_iteration_results_dir'] = \
        #    f"{self.file_manager_config['results_dir']}\\all_iteration_results"
        os.makedirs(self.file_manager_config['results_dir'])
        os.makedirs(self.file_manager_config['test_logs_dir'])
        # os.mkdir(self.file_manager_config['all_iteration_results_dir'])
        self.file_manager_config['no_results_file'] = f"{self.file_manager_config['results_dir']}" \
                                                      f"\\no_results_recorded.txt"
        with open(self.file_manager_config['no_results_file'], "w") as no_res_file:
            no_res_file.write("There are no results in this directory so this \
                                     file can probably be deleted.")
        self.setup_data['date_time'] = self.file_manager_config['date_time']
        self.setup_data['results_dir'] = self.file_manager_config['results_dir']
        self.setup_data['test_logs_dir'] = self.file_manager_config['test_logs_dir']

    def create_script_backup(self):
        '''
        Docs
        '''
        shutil.copytree(os.getcwd(),
                        f"{self.file_manager_config['results_dir']}\\test_scripts_backup\\tcmfw")

        shutil.copy2(self.file_manager_config['setup_file'],
                     f"{self.file_manager_config['results_dir']}\\test_scripts_backup\\")

        dst_file = f"{self.file_manager_config['results_dir']}\\test_scripts_backup\\" \
                   f"{os.path.basename(self.file_manager_config['setup_file'])}"
        new_file_name = f"{self.file_manager_config['results_dir']}\\test_scripts_backup\\" \
                        f"{self.file_manager_config['date_time']}" \
                        f"_{os.path.basename(self.file_manager_config['setup_file'])}"
        shutil.move(dst_file, new_file_name)

        self.file_manager_config['test_cases_backup_dir'] = f"{self.file_manager_config['results_dir']}\\test_scripts_backup\\test_cases"
        os.makedirs(self.file_manager_config['test_cases_backup_dir'])

        if self.setup_data.get('pathloss_file', '') != '':
            pathloss_file = os.path.abspath(f"..\\test_cases\\pathloss_files\\"
                                            f"{self.setup_data.get('pathloss_file', 'default_pathloss_file.csv')}")
            if os.path.isfile(pathloss_file):
                shutil.copy2(pathloss_file, f"{self.file_manager_config['results_dir']}\\test_scripts_backup\\")

    def backup_test_case(self, test_case_file='', file_dir='..\\test_cases'):
        '''
        Docs
        '''
        if not os.path.isabs(test_case_file):
            test_case_file = os.path.abspath(f'{file_dir}\\{test_case_file}')
        if os.path.isfile(test_case_file):
            if not os.path.isfile(f"{self.file_manager_config['test_cases_backup_dir']}\\{test_case_file}"):
                shutil.copy2(test_case_file, self.file_manager_config['test_cases_backup_dir'])

    def append_to_history_log(self):
        '''
        Docs
        '''
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
        '''
        Docs
        '''
        abs_file_path = os.path.join(self.results_dir, file_name)
        with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(file_info)

    def add_iteration_result_header(self, file_name, header):
        '''
        Docs
        '''
        abs_file_path = os.path.join(self.file_manager_config['all_iteration_results_dir'], file_name)
        with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header)

    def save_iteration_result(self, file_name, results):
        '''
        Docs
        '''
        if os.path.isfile(self.file_manager_config['no_results_file']):
            os.remove(self.file_manager_config['no_results_file'])
        abs_file_path = os.path.join(self.file_manager_config['all_iteration_results_dir'], file_name)
        with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(results)

    def add_final_result_header(self, file_name, header):
        '''
        Docs
        '''
        abs_file_path = os.path.join(self.results_dir, file_name)
        with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header)

    def save_final_result(self, file_name, results):
        '''
        Docs
        '''
        if os.path.isfile(self.file_manager_config['no_results_file']):
            os.remove(self.file_manager_config['no_results_file'])
        abs_file_path = os.path.join(self.results_dir, file_name)
        with open(abs_file_path + '.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(results)

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
            with open(abs_file_path, 'w') as definition_file:
                writer = csv.DictWriter(definition_file, definition_list[0].keys())
                writer.writeheader()
                writer.writerow({'run': 'START'})
                for dict_data in definition_list:
                    writer.writerow(dict_data)
                writer.writerow({'run': 'END'})
        except IOError as errno:
            print('bob '+errno)
        return

