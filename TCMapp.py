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
    TCMapp.py
    ~~~~~~~~~~~

    Module to provide an selection gui for running tests.

    :copyright: 2018 by Aaron Greenyer
    :license: MIT, see COPYING for more details.
"""

import os
import csv
import json
import subprocess
import PIL.Image
import io
import base64
import PySimpleGUI as sg

from optparse import OptionParser
from loguru import logger

from tcmfw.configure_logger import setup_logging

DEFAULT_CONFIG_FILE = os.path.normpath(f'{os.getcwd()}/station_config.json')

# default options
opt = {
    'setup_dir': os.path.normpath(f'{os.getcwd()}/setup_files'),  # default setup directory
    'test_queue_name': 'selected_test_queue.txt',
    'tcm_dir': os.path.normpath(f'{os.getcwd()}/tcmfw/'),
    'formats': '.json .csv', # extensions of files to be listed; space delimited
    'output_encoding': 'autodetect', # any valid encoding ('utf-8', 'utf-16le', etc) or autodetect.
    'backup_ext': '.bak', # extension of backed up files. Use something not in 'formats' to prevent backups from showing in the dropdown list.
    }

def convert_to_bytes(file_or_bytes=None, resize=None):
    '''
    Will convert into bytes and optionally resize an image that is a file or a base64 bytes object.
    Turns into  PNG format in the process so that can be displayed by tkinter
    :param file_or_bytes: either a string filename or a bytes base64 image object
    :type file_or_bytes:  (Union[str, bytes])
    :param resize:  optional new size
    :type resize: (Tuple[int, int] or None)
    :return: (bytes) a byte-string object
    :rtype: (bytes)
    '''
    if isinstance(file_or_bytes, str):
        img = PIL.Image.open(file_or_bytes)
    else:
        try:
            img = PIL.Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = PIL.Image.open(dataBytesIO)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width*scale), int(cur_height*scale)), PIL.Image.ANTIALIAS)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()

def run_tcm_queue():

    tcm_dir = opt['tcm_dir']

    try:
        os.remove(f'{tcm_dir}/stop.txt')
        logger.debug('File: \'stop.txt\' removed. Clear to run test.')
    except FileNotFoundError:
        logger.debug('File: \'stop.txt\' not found. Clear to run test.')

    test_count = 1

    while test_count > 0:

        test_queue = read_test_queue()
        if 'FNF' in test_queue:
            logger.debug(f'File: \'selected_test_queue.txt\' not found.')
            return
        elif '@close' in test_queue:
            logger.debug(f'File: \'selected_test_queue.txt\' has @close.')
            return
        elif not test_queue:
            logger.debug(f'File: \'selected_test_queue.txt\' is blank.')
            return

        test_count = len(test_queue)
        logger.debug(f'Test Count: {test_count}')

        try:
            queue_file_out = open("selected_test_queue.txt", "w")
            if test_count > 0:
                queue_file_out.writelines('\n'.join(test_queue[1:]))
            else:
                queue_file_out.writelines('')
            queue_file_out.close()
        except Exception as ex:
            logger.exception(f'Unexpected error: {ex}')
            return

        if not os.path.exists(f'{tcm_dir}/stop.txt'):
            try:
                setup_csv_file_name = test_queue[0]
                logger.debug(setup_csv_file_name)
                logger.debug(f'Running: {setup_csv_file_name}')
                subprocess.run(['python', 'tcm.py', setup_csv_file_name], cwd=tcm_dir)
            except Exception as ex:
                logger.exception(f'Unexpected error: {ex}')
        else:
            logger.debug(f'{tcm_dir}/stop.txt Found')
            return

def wrap_up_queue():
    test_queue = read_test_queue()
    if 'FNF' in test_queue:
        logger.warning("File 'selected_test_queue.txt' is missing... Did you delete it?")
        return True
    elif '@close' in test_queue:
        logger.info("No Tests Selected")
    elif test_queue:
        logger.info("\n\tTests in the queue:")
        for csv_test_name in test_queue:
            logger.info(f"\t\t{csv_test_name}")

    try:
        os.remove("selected_test_queue.txt")
        logger.debug('\'selected_test_queue.txt\' file removed')
    except FileNotFoundError:
        logger.error(f"ERROR: Error removing file: selected_test_queue.txt")
    finally:
        if '@close' not in test_queue:
            # input("\n    +---------------------------------------------------+"
            #       "\n    |              Press enter to exit :)               |"
            #       "\n    +---------------------------------------------------+")
            sg.popup('Test session finished\n')

def load_dir_setup_files():
    try:
        fns = os.listdir(opt['setup_dir'])
    except Exception as ex:
        logger.error("could not load folder:", ex)
        return "invalid folder"

    file_types = [x.strip() for x in opt['formats'].split()]
    setup_files_list = [fn for fn in fns if any(fn.endswith(x) for x in file_types)]
    logger.debug(f'Loading files: {setup_files_list}')
    return setup_files_list


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


def auto_layout(d_cf):
    longest_key_len = 0
    for key in d_cf:
        longest_key_len = (longest_key_len, len(key))[len(key) > longest_key_len]
    lks = longest_key_len-5

    logger.debug(f'lks= {lks}')

    list_column = []
    element_dict = {
        'Text': sg.Text,
        'InputText': sg.InputText,
        'Combo': sg.Combo,
        'Spin': sg.Spin,
        'FolderBrowse': sg.FolderBrowse,
        'Button': sg.Button,
        'Output': sg.Output,
        'Input': sg.Input,
        'In': sg.In
        }
    try:
        for text_key, d_value in d_cf.items():
            row_elements = []
            row_elements.append(sg.Text(f'{str(text_key).capitalize().replace("_", " ")}: ', size=(lks, 1)))
            for element_key, element_args in d_value.items():
                if 'Image' in element_key:
                    row_elements.append(sg.Image(data=convert_to_bytes(
                        'C:/Users/Zircon/Desktop/python_projects/TCM/setup_files/default_test_image.png',
                        resize=(200, 300))))
                else:
                    locals().update(element_args)
                    arg_string = [arg_value for arg_value in element_args.values()]
                    row_elements.append(element_dict[element_key](**element_args))
            list_column += [[*row_elements]]
    except Exception as ex:
        list_column = [[sg.Text('Not a valid setup file')]]
    return list_column

                #logger.info(logger.info(f'{text_key}:\tsg.{element_key}([{}])' * (indent+1) + str(value)))

def table_example(setup_file):
    #filename = sg.popup_get_file('filename to open', no_window=True, file_types=(("CSV Files","*.csv"),))
    filename = setup_file
    setup_dir = opt['setup_dir']
    # --- populate table with file contents --- #
    #if filename == '':
    #    return
    data = []
    header_list = []
    #button = sg.popup_yes_no('Does this file have column names already?')
    button = 'No'
    logger.debug(f'{setup_dir}/{setup_file}')
    if filename is not None:
        with open(f'{setup_dir}/{setup_file}', "r") as infile:
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

    logger.debug(data)
    #logger.debug([str(filter(None, f'{row[0]}, {row[0]}')) for row in data])
    logger.debug([x for x in data if x[0]])

    # layout = [[sg.Table(values=data,
    #                         headings=header_list,
    #                         max_col_width=25,
    #                         auto_size_columns=True,
    #                         justification='right',
    #                         # alternating_row_color='lightblue',
    #                         num_rows=min(len(data), 20))]]

    filtered_list = [x for x in data if x[0]]
    logger.debug(filtered_list)
    lks = text_aligner({row[0]: row[1] for row in filtered_list})
    layout = [[sg.Text(f'{str(row[0]).capitalize().replace("_", " ")}: ', size=(lks, 1)), sg.In(default_text=f'{row[1]}')] for row in filtered_list]
    setup_frame = [[sg.Column(layout, scrollable=True, size=(550, 435))]]
    setup_frame = [[sg.Frame(filename, setup_frame, font=['Helvetica', 14, 'bold'], key='-SETUP-FRAME-')]]
    setup_frame += [[sg.Save("Save Changes")]]

    return setup_frame

def build_setup_file_frame(setup_file):
    setup_dir = opt['setup_dir']
    with open(f'{setup_dir}/{setup_file}') as f:
        setup_file_dict = json.load(f)

    #pretty(setup_file_dict)
    setup_frame = auto_layout(setup_file_dict)
    setup_frame = [[sg.Column(setup_frame, scrollable=True, size=(550, 435))]]
    setup_frame = [[sg.Frame(setup_file, setup_frame, font=['Helvetica', 14, 'bold'], key='-SETUP-FRAME-')]]
    setup_frame += [[sg.Save("Save Changes")]]
    return setup_frame


def queue_builder_frame():
    return [
        [
            sg.Column([[sg.Text('Setup Files', font=['Helvetica', 12, 'bold'])], [
                sg.Listbox(values=[], size=(30, 12),
                           key='-SETUP-LIST-', enable_events=True)]]),
            sg.Column([[sg.Button('Add -->', size=(6, 1))], [sg.Button('Remove', size=(6, 1))], [sg.Button('Clear', size=(6, 1))]]),
            sg.Column([[sg.Text('Run Queue', font=['Helvetica', 12, 'bold'])],
                       [sg.Listbox(values=[], size=(30, 12), key='-QUEUE-')]]),
        ],
        [sg.Text(pad=(235, 0)), sg.Button('Run Tests', )]
    ]

def setup_selection_frame():
    return [[sg.Text('Setup Files Location', font=['Helvetica', 12, 'bold'])],
            [sg.Input(default_text='C:\\Users\\user\\test_dir\\setup_files', size=(75, 1), key='-SETUP-FOLDER-', readonly=True, enable_events=True),
             sg.FolderBrowse(button_text='...', key='-SETUP-BROWSE-', target='-SETUP-FOLDER-', initial_folder=opt['setup_dir'])]]

def station_id_frame(cf_data):
    lks = text_aligner(cf_data)
    data_layout = [[sg.Text(f'{str(key).capitalize().replace("_", " ")}: ', size=(lks, 1), font=['Helvetica', 12, 'bold']), sg.Text(f'{value: <48}')] for key, value in cf_data.items()]
    return [[sg.Frame('Station ', data_layout, font=['Helvetica', 14, 'bold']), sg.Image(data=convert_to_bytes('pc_icon.png', resize=(130, 130)))]]

def test_queue_viewer(config_fn):
    with open(config_fn) as f:
        station_cf_data = json.load(f)

    station_id_layout = station_id_frame(station_cf_data)
    setup_selection_layout = setup_selection_frame()
    queue_layout = queue_builder_frame()

    file_list_column = station_id_layout + setup_selection_layout + queue_layout
    with open('default_example.json') as f:
        setup_data = json.load(f)
    layout = [
        [
            sg.Column(file_list_column),
            #sg.VSeperator(),
            #sg.Column(),
        ]
    ]

    # Create the window
    window = sg.Window("Queue Viewer").layout(layout).finalize()
    blank_window = sg.Window("Setup File", size=(0, 0), location=(2000, 200)).layout([[]]).finalize()
    table_window = sg.Window("Setup File", size=(0, 0), location=(2000, 200)).layout([[]]).finalize()
    setup_window = sg.Window("Setup File", size=(0, 0), location=(2000, 200)).layout([[]]).finalize()
    blank_window.close()
    table_window.close()
    setup_window.close()

    window['-SETUP-LIST-'].update(values=load_dir_setup_files())
    #window['-SETUP-FRAME-'].update(visible=False)

    logger.debug(f'{window.size} {window.current_location()}')
    #logger.debug(f'{setup_window.size} {setup_window.current_location()}')
    # Create an event loop
    while True:
        event, values = window.read()
        # End program if user closes window or
        # presses the OK button
        if event == sg.WIN_CLOSED:
            break
        main_window_size = window.size
        main_window_location = window.current_location()
        logger.debug(f'{event}, {values}, {window.size}')
        if "?" in event:
            sg.popup('{}'.format(values[event+'v']))
        if "-SETUP-LIST-" in event:
            if values['-SETUP-LIST-']:
                new_win_loc = [main_window_size[0]+main_window_location[0], main_window_location[1]]
                logger.debug(new_win_loc)
                blank_window = sg.Window("Setup File", size=main_window_size, location=new_win_loc).layout([[]]).finalize()
                setup_window.close()
                table_window.close()
                if '.csv' in values['-SETUP-LIST-'][0]:
                    table_window = sg.Window("Setup File", size=main_window_size, location=new_win_loc).layout(table_example(values['-SETUP-LIST-'][0])).finalize()
                    blank_window.close()
                if '.json' in values['-SETUP-LIST-'][0]:
                    setup_window = sg.Window("Setup File", size=main_window_size, location=new_win_loc).layout(
                        build_setup_file_frame(values['-SETUP-LIST-'][0])).finalize()
                    blank_window.close()
        #     if values['-SETUP-LIST-']:
        #         window['-setup-view-help-'].update(visible=False)
        #         if 'setup example' in values['-SETUP-LIST-']:
        #             window['-SETUP-FRAME-'].update(visible=True)
        #         else:
        #             window['-SETUP-FRAME-'].update(visible=False)
        if "Add -->" in event:
            if values['-SETUP-LIST-']:
                queue = window['-QUEUE-'].get_list_values()
                queue.extend(values['-SETUP-LIST-'])
                #sg.popup('{}'.format(queue))
                window['-QUEUE-'].update(values=queue)
        if "Remove" in event:
            if values['-QUEUE-']:
                queue = window['-QUEUE-'].get_list_values()
                queue_index = window['-QUEUE-'].get_indexes()[0]
                queue.pop(queue_index)
                window['-QUEUE-'].update(values=queue)
        if "Clear" in event:
            window['-QUEUE-'].update(values=[])
        if '-SETUP-FOLDER-' in event:
            if values['-SETUP-BROWSE-'] != '':
                opt['setup_dir'] = values['-SETUP-BROWSE-']
                logger.debug(opt['setup_dir'])
                window['-QUEUE-'].update(values=[])
                window['-SETUP-LIST-'].update(values=load_dir_setup_files())
                blank_window.close()
                setup_window.close()
                table_window.close()
        if "Run Tests" in event:
            if window['-QUEUE-'].get_list_values():
                test_queue = window['-QUEUE-'].get_list_values()
                with open("selected_test_queue.txt", 'w') as selected_test_queue_file:
                    selected_test_queue_file.write('\n'.join(test_queue))
                logger.debug('{}'.format('\n'.join(test_queue)))
                break

    blank_window.close()
    table_window.close()
    setup_window.close()
    window.close()

def read_test_queue():
    queue_file = os.path.normpath('selected_test_queue.txt')
    if not os.path.exists(queue_file):
        return 'FNF'
    logger.debug(f'File Exists: {queue_file}')
    with open(queue_file, 'r') as qf:
        current_test_queue = [queue_item for queue_item in qf.read().split('\n') if queue_item.strip() != '']
    return current_test_queue

def check_for_current_test():
    test_queue_exists = True
    logger.debug('Searching for the selected_test_queue.txt file to see if there is a test running.')
    test_queue = read_test_queue()
    if 'FNF' in test_queue:
        logger.debug(f'No queue found. TCM Application Starter is clear to run.')
        test_queue_exists = False
        return test_queue_exists

    logger.debug("\tFile 'selected_test_queue.txt' already exists")

    if test_queue:
        logger.debug("\tTests in the queue:")
        for csv_test_name in test_queue:
            logger.debug(f"\t\t{csv_test_name}")

    logger.debug("\tThere could be a test running.")
    logger.debug("\tIf there is no test is running, delete this file to run a new test.")

    layout = [[sg.Text('Test Queue Found:')],
              [sg.Text('There could be a test running.')],
              [sg.Checkbox('I want to delete the test queue', key='-DELETE-QUEUE-', size=(22, 1))],
              [sg.Button(button_text='Delete'), sg.Cancel()]]

    window = sg.Window('Check For Current Test', layout)

    while True:
        event, values = window.read()
        # End program if user closes window or
        # presses the Cancel button
        if event == "Cancel" or event == sg.WIN_CLOSED:
            break
        if "Delete" in event:
            if values['-DELETE-QUEUE-']:
                logger.debug("Test queue deleted")
                os.remove(os.path.normpath("selected_test_queue.txt"))
                test_queue_exists = False
                break

    window.close()
    return test_queue_exists


def create_station_config():
    config_created = False

    sg.popup('No config file exists in directory\n'
             'Please enter the details to create the Test Station')

    layout = [[sg.Text('Test Station Data')],
              [sg.Text('ID number:', size=(12, 1)), sg.InputText(key="station_id")],
              [sg.Text('Country location:', size=(12, 1)), sg.InputText(key="country")],
              [sg.Text('City location:', size=(12, 1)), sg.InputText(key="city")],
              [sg.Text('Description:', size=(12, 1)), sg.InputText(key="description")],
              [sg.Text('Script directory:', size=(12, 1)), sg.InputText(key="script_dir", default_text=os.getcwd()),
               sg.FolderBrowse(button_text='...', target='script_dir', initial_folder=os.getcwd())],

              [sg.Submit(), sg.Cancel()]]

    window = sg.Window('Window Title', layout)

    while True:
        event, values = window.read()
        # End program if user closes window or
        # presses the Cancel button
        if event == "Cancel" or event == sg.WIN_CLOSED:
            break
        if "Submit" in event:
            logger.debug(values)
            del values['...']
            config_created = True
            with open('.station_config.json', 'w') as f:
                json.dump(values, f, indent=2)
            break
    window.close()

    return config_created


def main(config_options):
    station_config = os.path.normpath(config_options.config)
    sg.theme(config_options.theme)

    if not os.path.exists(station_config):
        logger.debug(f"File does not exists: {station_config}")
        if not create_station_config():
            return  # user has cancelled the config creator. exit the program

    logger.debug('________TCM Application________')
    logger.debug('Application Starter GUI')

    if not check_for_current_test():
        test_queue_viewer(station_config)

    if 'FNF' not in read_test_queue():
        run_tcm_queue()

    wrap_up_queue()


if __name__ == "__main__":
    """
    Docs
    """
    opts = OptionParser(usage='GUI for creating a test sequence.')
    opts.add_option("--config", help="Choose config file location", default=DEFAULT_CONFIG_FILE)
    opts.add_option("--debug", help="Overwrite config and enable logger debugging.", action="store_true", default=True)
    opts.add_option("--theme", help="Choose a theme from pysimplegui", default="System Default 1")

    (options, args) = opts.parse_args()

    setup_logging({'log_console_level': ('INFO', 'DEBUG')[options.debug]})  # TCMapp.py is a basic setup script and doesn't require logging to a file
    logger.debug(f'Option Settings: {options}')

    try:
        main(options)
    except KeyboardInterrupt:
        logger.warning('Keyboard Interrupt from user')
    except FileNotFoundError as ex:
        logger.error(f"ERROR: Setup File Not Found: {ex}")
    except Exception as ex:
        if options.debug:
            logger.exception(ex)
        else:
            logger.error(f'Fatal error!\n\nTest sequence generator crashed.\n\nReason: {str(ex)}')
        sg.popup(f'Fatal error!\n\nTest sequence generator crashed.\n\nReason: {str(ex)}')