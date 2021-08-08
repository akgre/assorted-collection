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
    test_flow_control.py
    ~~~~~~~~~~~

    Module to provide test flow control for the TCM application.

    :copyright: 2018 by Aaron Greenyer
    :license: MIT, see COPYING for more details.
"""

import os
import csv
import time
import json
import PySimpleGUI as sg

from optparse import OptionParser
from loguru import logger

from configure_logger import setup_logging

DEFAULT_CONFIG_FILE = os.path.normpath(f'{os.getcwd()}/../station_config.json')

# default options
opt = {
    'default_status_file': f'{os.getcwd()}/tcm_data.json',
    'formats': '.json',  # extensions of files to be listed; space delimited
    'output_encoding': 'autodetect',  # any valid encoding ('utf-8', 'utf-16le', etc) or autodetect.
    'backup_ext': '.bak',
    # extension of backed up files. Use something not in 'formats' to prevent backups from showing in the dropdown list.
}


# class FlowControl:
#     def __init__(self):
#         # flag files in local directory:
#         signal.signal(signal.SIGINT, self.signal_handler)
#         self.stopFile     = 'stop.txt'      # stop now
#         self.stopNextFile = 'stopNext.txt'  # stop before next test
#         self.stopLastFile = 'stopLast.txt'  # stop after last test in current set of tests
#         self.pauseFile    = 'pause.txt'     # pause
#         self.updateStatus = ''              # status message container
#         self.flag_dict = {'stop.txt': self.stop,
#                           'stopNext.txt': self.stop,
#                           'stopLast.txt': self.stop,
#                           'pause.txt': self.stop}
#
#         logger.debug('delete all flag files in local directory')
#         for flag_file in [self.stopFile, self.stopNextFile, self.stopLastFile, self.pauseFile]:
#             try:
#                 os.remove(flag_file)
#                 logger.debug(f'{flag_file} removed')
#             except:
#                 pass
#
#     def signal_handler(self, signal_name, frame):
#         print('Press Ctrl+C')
#
#     def update_info(self, field, info):
#         '''
#         This function writes data into the commsfile.txt file so that the gui can pick it up and display it.
#         The first argument is the field to be updated, the second line is the actual data. Both args are strings.
#         valid field types are: 'text',
#         '''
#         std = self.common['STD']
#         fileid = open("commsfile.txt", 'w')
#         fileid.write(field + "\n")
#         fileid.write(std + ' ' + info)
#         fileid.close()
#
#     def delay(self, s):
#         '''delays the script for s seconds'''
#         if s == 0:
#             pass
#         elif s <= 4:
#             time.sleep(s)
#         elif s > 4:
#             # logger.info(f'delay for {s} seconds')
#             for t in range(0, s):# tqdm()
#                 self.poll_status()
#                 #print(f'{chr(9608)*(s-t):{chr(9702)}<{s}}', end = '\r')
#                 logger.opt(raw=True).info(f"Delay for {s} seconds: {s-t:02d}\r")
#                 time.sleep(1)
#             # logger.opt(raw=True).info('\n')
#         return
#
#     def loop(self):
#         print(' '*100, end = '\r')
#         for x in range(0, 80):
#             self.poll_status()
#             print(f'{chr(9608)*x}', end = '\r')
#             time.sleep(0.05)
#         for x in range(0, 80):
#             self.poll_status()
#             print(f'{" "*x}', end = '\r')
#             time.sleep(0.05)
#         print(' ' * 100, end='\r')
#
#     def skip_delay(self):
#         raise NotImplementedError
#
#     def pause(self):
#         raise NotImplementedError
#
#     def pause_for_user_input(self):
#         raise NotImplementedError
#
#     def stop(self):
#         raise Exception("test_stopped")
#
#     def shutdown(self):
#         raise Exception("test_stopped")
#
#     def poll_status(self):
#         flag_files = []
#         for file_name in glob.glob(f'{os.getcwd()}/*.txt'):
#             flag_files.append(os.path.basename(file_name))
#
#         for flag in flag_files:
#             if self.flag_dict.get(flag):
#                 self.flag_dict[flag]()
class FlowCommands:
    def __init__(self):
        # flag files in local directory:
        self.stopFile = 'stop.txt'      # stop now
        self.pauseFile = 'pause.txt'  # pause
        self.resumeFile = 'resume.txt'     # pause
        self.nextFile = 'next.txt'  # stop before next test
        self.nextGroupFile = 'nextgroup.txt'  # stop after last test in current set of tests
        self.updateStatus = ''              # status message container
        self.flag_list = ['stop.txt', 'pause.txt', 'resume.txt', 'next.txt', 'nextgroup.txt']

    def remove_commands(self):
        try:
            fns = os.listdir(os.getcwd())
        except Exception as ex:
            logger.error("could not load folder:", ex)
            return "invalid folder"
        file_types = [x.strip() for x in ['.txt']]
        setup_files_list = [fn for fn in fns if any(fn.endswith(x) for x in file_types)]
        logger.debug(f'Loading files: {setup_files_list}')
        for file in setup_files_list:
            if os.path.basename(file) in self.flag_list:
                os.remove(file)
        return setup_files_list

    def stop(self):
        self.remove_commands()
        try:
            fs = open(self.stopFile, 'w+')
        except:
            logger.error('StopMainFrame.py stopFunction ERROR: cannot create ' + self.stopFile + '\n')
            return False
        #  t = time.ctime(time.time())
        fs.write('stop')
        fs.close()

    def pause(self):
        self.remove_commands()
        try:
            fs = open(self.pauseFile, 'w+')
        except:
            logger.error('StopMainFrame.py stopFunction ERROR: cannot create ' + self.pauseFile + '\n')
            return False
        # t = time.ctime(time.time())
        fs.write('pause')
        fs.close()

    def resume(self):
        self.remove_commands()
        try:
            fs = open(self.resumeFile, 'w+')
        except:
            logger.error('StopMainFrame.py stopFunction ERROR: cannot create ' + self.resumeFile + '\n')
            return False
        # t = time.ctime(time.time())
        fs.write('resume')
        fs.close()

    def next(self):
        self.remove_commands()
        try:
            fs = open(self.nextFile, 'w+')
        except:
            logger.error('StopMainFrame.py stopFunction ERROR: cannot create ' + self.nextFile + '\n')
            return False
        #t = time.ctime(time.time())
        fs.write('next')
        fs.close()

    def next_group(self):
        self.remove_commands()
        try:
            fs = open(self.nextGroupFile, 'w+')
        except:
            logger.error('StopMainFrame.py stopFunction ERROR: cannot create ' + self.nextGroupFile + '\n')
            return False
        #t = time.ctime(time.time())
        fs.write('next group')
        fs.close()


class TestStatusData:
    def __init__(self, tcm_data_file=None):

        self.status_file = None
        self.station_data = {}
        self.setup_data = {}
        self.test_case_files = {}
        self.test_definitions = {}
        self.test_brief = {}
        self.test_messages = {}
        self.test_results_brief = {}
        self.flag_changes = []

        self.update_status_file(tcm_data_file)

    def update_status_file(self, status_file_name):
        status_file = os.path.normpath(status_file_name)
        if not os.path.exists(status_file):
            logger.debug(f"File does not exists {status_file}")
            return False

        self.status_file = status_file

    def verify_status_file(self):
        for attempt in range(0, 10):
            try:
                with open(self.status_file, 'r') as f:
                    status_data = json.load(f)
                return status_data
            except:
                logger.debug(f"File can not be opened. Attempt {attempt} {self.status_file}")
            time.sleep(0.5)
        raise

    def read_status_file(self):
        status_data = self.verify_status_file()
        #pretty_dict(status_data)
        return status_data

    def update_status_data(self):
        status_data = self.read_status_file()
        if self.station_data != status_data['station_data']:
            self.flag_changes.append('station_data')
            self.station_data.update(status_data['station_data'])
        if self.setup_data != status_data['setup_data']:
            self.flag_changes.append('setup_data')
            self.setup_data.update(status_data['setup_data'])
        if self.test_case_files != status_data['test_case_files']:
            self.flag_changes.append('test_case_files')
            self.test_case_files.update(status_data['test_case_files'])
        if self.test_definitions != status_data['test_definitions']:
            self.flag_changes.append('test_definitions')
            self.test_definitions.update(status_data['test_definitions'])
        if self.test_brief != status_data['test_brief']:
            self.flag_changes.append('test_brief')
            self.test_brief.update(status_data['test_brief'])
        if self.test_messages != status_data['test_messages']:
            self.flag_changes.append('test_messages')
            self.test_messages.update(status_data['test_messages'])
        if self.test_results_brief != status_data['test_results_brief']:
            self.flag_changes.append('test_results_brief')
            self.test_results_brief.update(status_data['test_results_brief'])

    def get_data_changes(self):
        return self.flag_changes

    def clear_flag_changes(self, flag):
        if flag in self.flag_changes:
            self.flag_changes.remove(flag)


def pretty_dict(d, indent=0):
    for key, value in d.items():
        logger.info('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty_dict(value, indent+1)
        else:
            logger.info('\t' * (indent+1) + str(value))

def text_aligner(_dict):
    longest_key_len = 0
    for key in _dict.keys():
        longest_key_len = (longest_key_len, len(key))[len(key) > longest_key_len]

    logger.debug(longest_key_len)
    return longest_key_len

# def table_frame(setup_file=None):
#     #filename = sg.popup_get_file('filename to open', no_window=True, file_types=(("CSV Files", "*.csv"),))
#     # --- populate table with file contents --- #
#     #if filename == '':
#     #    return
#     data = []
#     header_list = []
#     #button = sg.popup_yes_no('Does this file have column names already?')
#     button = 'Yes'
#     filename = 'C:/Users/Zircon/Desktop/python_projects/TCM/test_cases/sensitivity/complie_sens_results.csv'
#     if filename is not None:
#         with open(filename, "r") as infile:
#             reader = csv.reader(infile)
#             if button == 'Yes':
#                 header_list = next(reader)
#             try:
#                 data = list(reader)  # read everything else into a list of rows
#                 if button == 'No':
#                     header_list = ['column' + str(x) for x in range(len(data[0]))]
#             except:
#                 sg.popup_error('Error reading file')
#                 return
#     sg.set_options(element_padding=(0, 0))
#
#     layout = [[sg.Table(values=data,
#                         key='-TABLE-',
#                         headings=header_list,
#                         max_col_width=25,
#                         auto_size_columns=True,
#                         justification='right',
#                         select_mode='none',
#                         size=(500, 200),
#                         # alternating_row_color='lightblue',
#                         num_rows=min(len(data), 20))]]
#     return [[sg.Column(layout, size=(500, 200), scrollable=True)]]
#     #window = sg.Window('Table', layout, grab_anywhere=False)
#     #event, values = window.read()

def results_brief_frame(test_brief=None):
    results_brief_file = test_brief['results_brief_file']
    data = []
    header_list = []
    button = 'Yes'
    if results_brief_file is not None:
        with open(results_brief_file, 'r') as infile:
            reader = csv.reader(infile)
            if button == 'Yes':
                header_list = next(reader)
            try:
                data = list(reader)  # read everything else into a list of rows
                if button == 'No':
                    header_list = ['column' + str(x) for x in range(len(data[0]))]
            except:
                sg.popup_error('Error reading file')
                return
    sg.set_options(element_padding=(0, 0))

    #header_list = ['column' + str(x) for x in range(len(data[0]))]
    layout = [[sg.Table(values=data,
                        key='-RESULTS-TABLE-',
                        headings=header_list,
                        auto_size_columns=True,
                        justification='left',
                        select_mode='none',
                        selected_row_colors=('black', 'SteelBlue1'),
                        # alternating_row_color='lightblue',
                        num_rows=min(len(data), 20))]]
    return layout
    #window = sg.Window('Table', layout, grab_anywhere=False)
    #event, values = window.read()

def table_frame(test_definitions):
    #data = test_definitions['test_definition_list']
    data = [['', '', '', '', '', '']for x in range(0, 10)]
    header_list = ['  ', 'Test ID', 'Description                ', 'Value  ','Unit  ', 'Status']
    # if filename is not None:
    #     with open(filename, "r") as infile:
    #         reader = csv.reader(infile)
    #         if button == 'Yes':
    #             header_list = next(reader)
    #         try:
    #             data = list(reader)  # read everything else into a list of rows
    #             if button == 'No':
    #                 header_list = ['column' + str(x) for x in range(len(data[0]))]
    #         except:
    #             sg.popup_error('Error reading file')
    #             return
    # sg.set_options(element_padding=(0, 0))

    #header_list = ['column' + str(x) for x in range(len(data[0]))]
    layout = [[sg.Table(values=data,
                        key='-DEF-TABLE-',
                        headings=header_list,
                        auto_size_columns=True,
                        justification='left',
                        select_mode='none',
                        selected_row_colors=('black', 'SteelBlue1'),
                        # alternating_row_color='lightblue',
                        num_rows=min(len(data), 20))]]
    return [[sg.Text(' '*100, key='-CURRENT-TEST-')]]+layout
    #window = sg.Window('Table', layout, grab_anywhere=False)
    #event, values = window.read()



def output_frame():
    return [[sg.Text(f'Test Messages', font=['Helvetica', 16, 'bold'])],
            [sg.Output(size=(70, 18), key='-OUTPUT-')],
            [sg.Text(f'Script Status: Running', key='-CURRENT-STATE-', size=(20, 1))],]

def setup_data_frame(setup_data):
    lks = text_aligner(setup_data)
    #pretty(setup_file_dict)

    setup_frame = [[sg.Text(f'{str(key).capitalize().replace("_", " ")}: ', size=(lks, 1), font=['Helvetica', 12, 'bold']), sg.Text(f'{value}')] for key, value in setup_data.items()]
    setup_frame = [[sg.Column(setup_frame, scrollable=True, size=(550, 435))]]
    setup_layout = [[sg.Frame(setup_data['setup_file'], setup_frame, font=['Helvetica', 14, 'bold'], key='-SETUP-FRAME-')]]
    return setup_layout

def station_id_frame(id_data):
    lks = text_aligner(id_data)
    pretty_dict(id_data)

    data_layout = [[sg.Text(f'{str(key).capitalize().replace("_", " ")}: ', size=(lks, 1), font=['Helvetica', 12, 'bold']), sg.Text(f'{value}')] for key, value in id_data.items()]
    return [[sg.Frame('Station ', data_layout, font=['Helvetica', 14, 'bold'], )]]

def progress_frame(test_case_data):
    test_case_list = test_case_data['test_case_list']
    bar_size = (int(46/len(test_case_list)), 20)
    pb_layout = [[sg.ProgressBar(1, orientation='h', size=bar_size, key=test, pad=(1,1)) for test in test_case_list]]
    title = [[sg.Text(f'Test Status', font=['Helvetica', 16, 'bold']), sg.Text(f'                                                                      '),
             sg.Button("Show Details", key='show_details', size=(10, 1), pad=(2, 2))],]
    return title+pb_layout
    #      sg.Button("Show Details", key='show_details', size=(10, 1), pad=(2, 2))],
    # return [
    #     [sg.Text(f'Test Status', font=['Helvetica', 16, 'bold']), sg.Text(f'                                                                            '),
    #      sg.Button("Show Details", key='show_details', size=(10, 1), pad=(2, 2))],
    #     [sg.ProgressBar(1, orientation='h', size=bar_size, key='progbar', bar_color=('green', '#D0D0D0'), pad=(1,1)),
    #      sg.ProgressBar(1, orientation='h', size=bar_size, key='progbar2', bar_color=('yellow', '#D0D0D0'), pad=(1,1)),
    #      sg.ProgressBar(1, orientation='h', size=bar_size, key='progbar3', bar_color=('red', '#D0D0D0'), pad=(1,1)),],
    #     [sg.Text('')]]

def control_frame(setup_data):
    flow_control_level = setup_data['flow_control_level']
    cf_layout = [[sg.Button('Stop', size=(10, 2), pad=(3, 3)), #button_color=('black', 'IndianRed1')),
                  sg.Button('Pause', key='Pause', size=(10, 2), pad=(3, 3)),  #button_color=('black', 'khaki')),
                  sg.Button('Next', size=(10, 2), pad=(3, 3)),  #button_color=('black', 'SteelBlue1')),
                  sg.Button('Next Group', size=(10, 2), pad=(3, 3)), # button_color=('black', 'RoyalBlue2')),
                  sg.Text('   '),
             sg.Button('Results Brief', size=(12, 2), pad=(3, 3))]]

    if 'DEBUG' in flow_control_level:
        cf_layout += [[sg.Spin(values=[100], pad=((5,0), (0,0))), sg.Text('s  Debug delay', pad=((0,5), (0,0))), sg.Checkbox(text='Debug Halt')]]

    return cf_layout

def update_ui(window, status_data):
    if 'station_data' in status_data.flag_changes:
        print('WARNING: Change detected in station data. This should not change')
        status_data.clear_flag_changes('station_data')
    if 'setup_data' in status_data.flag_changes:
        print('WARNING: Change detected in setup data. This should not change')
        status_data.clear_flag_changes('setup_data')
    if 'test_case_files' in status_data.flag_changes:
        print('TEST UPDATE: Change detected in test case history')
        for test in status_data.test_case_files["test_case_list"]:
            if test in status_data.test_case_files["test_case_history"]:
                window[test].update_bar(1)
            else:
                window[test].update_bar(0)
        status_data.clear_flag_changes('test_case_files')
    if 'test_definitions' in status_data.flag_changes:
        status_data.clear_flag_changes('test_definitions')
    if 'test_messages' in status_data.flag_changes:
        status_data.clear_flag_changes('test_messages')
    if 'test_brief' in status_data.flag_changes:
        print('TEST UPDATE: Change detected in test test brief')
        test_definition_list = status_data.test_brief['test_definition_list']
        current_test_case = status_data.test_case_files['current_test_case']
        window['-DEF-TABLE-'].update(values=test_definition_list)
        window['-CURRENT-TEST-'].update(value=f'Test case file: {current_test_case}')
        for row in test_definition_list:
            if '▶' in row[0]:
                window['-DEF-TABLE-'].update(select_rows=[test_definition_list.index(row)])
                window['-DEF-TABLE-'].update(select_rows=[test_definition_list.index(row)])
        status_data.clear_flag_changes('test_brief')
    if 'test_results_brief' in status_data.flag_changes:
        status_data.clear_flag_changes('test_results_brief')


def flow_control_viewer():
    status_data = TestStatusData(opt['default_status_file'])
    flow_control = FlowCommands()
    status_data.update_status_data()


    progress_layout = progress_frame(status_data.test_case_files)
    #status_data.clear_flag_changes('test_case_files')
    test_view_layout = table_frame(status_data.test_definitions)
    #status_data.clear_flag_changes('test_definitions')
    output_layout = output_frame()
    control_layout = control_frame(status_data.setup_data)
    #status_data.clear_flag_changes('test_messages')

    station_id_layout = station_id_frame(status_data.station_data)
    #status_data.clear_flag_changes('station_data')
    setup_layout = setup_data_frame(status_data.setup_data)
    #status_data.clear_flag_changes('setup_data')
    #status_data.clear_flag_changes('test_brief')
    #status_data.clear_flag_changes('test_results_brief')

    layout = [
        [
            sg.Column(progress_layout+test_view_layout+control_layout+output_layout),
            sg.Column([[sg.Text('  ')]]),  # blank separator
            sg.Column(station_id_layout+setup_layout, visible=False, key='-DATA-VIEW-'),
        ]
    ]

    window = sg.Window("Test Flow Monitor", location=(300, 200)).layout(layout).finalize()
    results_brief_window = sg.Window("Results Brief", size=(0, 0), location=(2000, 200)).layout([[]]).finalize()
    results_brief_window.close()

    update_ui(window, status_data)

    row = 0
    while True:
        event, values = window.read(timeout=1000)
        # End program if user closes window or
        # presses the OK button
        logger.debug(values)
        if event == sg.WIN_CLOSED:
            flow_control.stop()
            break
        main_window_size = window.size
        main_window_location = window.current_location()
        logger.debug(event)
        logger.debug(values)
        logger.debug(f'{main_window_size}{main_window_location}')
        if event == "show_details":
            if window['-DATA-VIEW-'].visible:
                #window.size = (560, 560)
                window['-DATA-VIEW-'].update(visible=False)
                window['show_details'].update(text='Show Details')
            else:
                #window.size = (1050, 560)
                window['-DATA-VIEW-'].update(visible=True)
                window['show_details'].update(text='Hide Details')


        if event == "Pause":
            icon = '▶'
            data = window['-DEF-TABLE-'].Values
            data[row][0] = icon
            data[row][4] = 'Pass'
            if row > 0:
                data[row-1][0] = ''
            window['-DEF-TABLE-'].update(values=data)
            window['-DEF-TABLE-'].update(select_rows=[row])
            row += 1
            if 'Pause' in window['Pause'].get_text():
                flow_control.pause()
                window['-CURRENT-STATE-'].update(value='Test Paused')
                window['Pause'].update(text='Resume', button_color=('black', 'dark sea green'))
            elif 'Resume' in window['Pause'].get_text():
                flow_control.resume()

                window['Pause'].update(text='Pause', button_color=('white', '#082567')) #  , button_color=('black', 'khaki'))

        if event == "Stop":
            confirm = sg.popup_ok_cancel('Are you sure you would like to stop the test?')
            logger.debug(confirm)
            if 'OK' == confirm:
                flow_control.stop()
                window['-CURRENT-STATE-'].update(value='Waiting for test to stop')
                window['Stop'].update(disabled=True)
                window['Pause'].update(disabled=True)
                window['Next'].update(disabled=True)
                window['Next Group'].update(disabled=True)
        if event == "Next":
            flow_control.next()
        if event == "Next Group":
            flow_control.next_group()

        if event == 'Results Brief':
            if results_brief_window:
                results_brief_window.close()
            results_brief_window = sg.Window("Results Brief").layout(results_brief_frame(status_data.test_results_brief)).finalize()


        status_data.update_status_data()
        logger.debug(status_data.flag_changes)
        if status_data.flag_changes:
            update_ui(window, status_data)

    results_brief_window.close()
    window.close()

def main(config_options):
    sg.theme("System Default")

    flow_control_viewer()



if __name__ == "__main__":
    """
    Docs
    """
    opts = OptionParser(usage='GUI for controlling the test flow.')
    opts.add_option("--config", help="Choose config file location", default=DEFAULT_CONFIG_FILE)
    opts.add_option("--debug", help="Overwrite config and enable logger debugging.", action="store_true", default=True)
    (options, args) = opts.parse_args()

    setup_logging({'log_console_level': ('INFO', 'DEBUG')[options.debug]})
    logger.debug(f'Options: {options}')

    try:
        main(options)
    except Exception as ex:
        logger.error("Fatal error!\n\nTest sequence generator crashed.\n\n" + str(ex))
        sg.popup("Fatal error!", "Test sequence generator crashed.\n\n" + str(ex))
        raise
