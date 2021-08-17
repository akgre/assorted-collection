"""
    Doc
"""
import os
import time
import yaml
import PIL.Image
import io
import base64
import PySimpleGUI as sg

from pathlib import Path
from loguru import logger

# load global options dictionary
opt_fn = "app_options.yaml"

# default options
opt = {
    'station_config_file': None,  # station file is used to identify the current machine
    'queue_file_name': 'selected_queue.yaml',  # name given to the file holding the queue.
    'queue_running_flag': False,  # flag used to indicate there is a current session in progress
    'previous_queue_list': None,  # If a session has stopped early, save queue here and delete the queue file. The queue file prevents any new sessions.
    'theme': 'System Default 1',  # Chooses a theme for the gui
    'file_dir': None,  # last seen directory for the file list. currently only run files from the same location.
    'icon': '../queue_scripts/assets/pc_icon.png',  # location for the station ID icon. makes it look more interesting
    'geometry': None,  # remember the size from the previous session
    'position': None,  # remember the location from the previous session
    'save_position': True,  # save the geometry and position of the window and restore on next load
    'MS_format_output': True,  # convert output to microsoft .NET style
    'formats': '.config .xml .json .py',  # extensions of files to be listed; space delimited
    'entrybox_width': 50,  # width of the entry boxes
    'output_encoding': 'autodetect', # any valid encoding ('utf-8', 'utf-16le', etc) or autodetect.
    'backup_ext': '.bak', # extension of backed up files. Use something not in 'formats' to prevent backups from showing in the dropdown list.
    }

try:
    with open(opt_fn) as f:
        opt.update(yaml.load(f, Loader=yaml.FullLoader))
except FileNotFoundError as ex:
    logger.debug(f'Default options used due to {ex}')


# Utility Functions
# ------------------------------------------------------------------------------
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


def pretty_dict(d, indent=0):
    for key, value in d.items():
        logger.debug('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty_dict(value, indent+1)
        else:
            logger.debug('\t' * (indent+1) + str(value))


def text_aligner(_dict):
    longest_key_len = 0
    for key in _dict.keys():
        longest_key_len = (longest_key_len, len(key))[len(key) > longest_key_len]

    logger.debug(longest_key_len)
    return longest_key_len


def load_dir_files(selected_dir):
    logger.debug(f'Loading files from: {selected_dir}')
    try:
        fns = [file.name for file in Path(selected_dir).iterdir()]
    except Exception as ex:
        logger.error(f"could not load folder: {selected_dir} {ex}")
        return ["invalid folder"]

    file_types = [x.strip() for x in opt['formats'].split()]
    files_list = [fn for fn in fns if any(fn.endswith(x) for x in file_types)]
    logger.debug(f'Loading files: {files_list}')
    return files_list


# load a current queue file.
# ------------------------------------------------------------------------------
def read_queue(queue_file):
    try:
        with open(queue_file, 'r') as qf:
            current_queue = yaml.load(qf, Loader=yaml.FullLoader)
    except FileNotFoundError as ex:
        logger.info(f'Default options used due to {ex}')
        current_queue = None
    return current_queue


def load_queue_file(current_queue, queue_file_name):
    # a queue will only be removed when all the items have successfully run
    # If there is a queue available read the contents, otherwise return None to indicate a new queue be created
    if current_queue is None:
        # create an empty queue file
        return None

    return read_queue(current_queue)


# Frame layouts.
# ------------------------------------------------------------------------------
def station_id_frame(station_config_file):
    try:
        with open(station_config_file, 'r') as qf:
            station_config = yaml.load(qf, Loader=yaml.FullLoader)
    except FileNotFoundError:
        logger.info(f'Default options used due to {ex}')
        raise
    lks = text_aligner(station_config)
    data_layout = [[sg.Text(f'{str(key).capitalize().replace("_", " ")}: ', size=(lks, 1), font=['Helvetica', 12, 'bold']), sg.Text(f'{value}')] for key, value in station_config.items()]
    return [[sg.Frame('Station ID', data_layout, font=['Helvetica', 14, 'bold']), sg.Image(data=convert_to_bytes(str(Path(opt['icon']).resolve()), resize=(130, 130)))]]


def selection_frame(init_folder):
    return [[sg.Text('Files Location', font=['Helvetica', 12, 'bold'])],
            [sg.Input(default_text=init_folder, size=(92, 1), key='-LIST FOLDER-', readonly=True, enable_events=True),
             sg.FolderBrowse(button_text='...', key='-LIST BROWSE-', target='-LIST FOLDER-', initial_folder=init_folder)]]

def queue_builder_frame(queue_running_flag):
    queue_builder_layout = [
        [
            sg.Column([[sg.Text('File List', font=['Helvetica', 12, 'bold'])], [
                sg.Listbox(values=[], size=(39, 12),
                           key='-FILE LIST-', enable_events=True)]]),
            sg.Column([[sg.Button('Add -->', size=(6, 1))], [sg.Button('Remove', size=(6, 1))], [sg.Button('Clear', size=(6, 1))]]),
            sg.Column([[sg.Text('Run Queue', font=['Helvetica', 12, 'bold'])],
                       [sg.Listbox(values=[], size=(39, 12), key='-QUEUE-')]]),
        ],
    ]
    if not queue_running_flag:
        # if there is no queue make the run button available
        queue_builder_layout += [[sg.Text(pad=(295, 0)), sg.Button('Run Queue', )]]
    else:
        # if a queue already exists then prevent the user from running and only allow them to modify the current queue
        queue_builder_layout += [[sg.Text(text='A queue already exists. To run a new queue you must stop the running scripts', pad=(10, 0)), sg.Text(pad=(43, 0)), sg.Button('Modify Queue', )]]

    return queue_builder_layout

# Main Window
# ------------------------------------------------------------------------------
def queue_window(station_config_file, queue_running_flag):

    # if there is n file directory remembered select the current working directory
    if opt['file_dir'] is None:
        opt['file_dir'] = str(Path.cwd())
    logger.debug(opt['file_dir'])

    # create the station frame from the station config file
    station_id_layout = station_id_frame(station_config_file)
    # location of the selectable files. file_dir is used for the initial directory
    selection_layout = selection_frame(opt['file_dir'])
    # build the queue selection layout. use the flag to select the modify or run button
    queue_layout = queue_builder_frame(queue_running_flag)

    layout = station_id_layout + selection_layout + queue_layout
    if opt['position'] is not None and opt['save_position']:
        # use the last known position
        window = sg.Window("Queue Viewer", location=opt['position'], enable_close_attempted_event=True).layout(layout).finalize()
    else:
        #use centered position
        window = sg.Window("Queue Viewer", enable_close_attempted_event=True).layout(layout).finalize()

    # create references for additional windows
    # blank_windows is created to minimize flicker between selecting files contents to view
    blank_window = sg.Window("", size=(0, 0), location=(2000, 200)).layout([[]]).finalize()
    # table window is for viewing csv files
    table_window = sg.Window("", size=(0, 0), location=(2000, 200)).layout([[]]).finalize()
    # file window is for viewing a user created file.
    file_window = sg.Window("", size=(0, 0), location=(2000, 200)).layout([[]]).finalize()
    #close the windows, references will be used later
    blank_window.close()
    table_window.close()
    file_window.close()

    if opt['previous_queue_list'] is not None:
        sg.popup("Previous script stopped early. Loading remaining tests from the previous queue")
        logger.debug(opt['previous_queue_list'])
        window['-QUEUE-'].update(values=opt['previous_queue_list'])
        opt['previous_queue_list'] = None  # clear the previous queue. if user closes the gui they will now be lost.
    elif queue_running_flag is not None:
        window['-QUEUE-'].update(values=read_queue(opt['queue_file_name']))

    # update the file list with the files available in the current directory
    window['-FILE LIST-'].update(values=load_dir_files(opt['file_dir']))

    run_scripts = False  # flag to check the run button has been pressed
    while True:
        event, values = window.read()
        # End program if user closes window or
        # presses the OK button
        if event in ('-WINDOW CLOSE ATTEMPTED-', sg.WIN_CLOSED):
            opt['geometry'] = window.size
            opt['position'] = window.current_location()
            break
        logger.debug(f'{event}, {values}')
        if '-LIST FOLDER-' in event:
            if values['-LIST BROWSE-'] != '':
                opt['file_dir'] = values['-LIST BROWSE-']
                logger.debug(opt['file_dir'])
                window['-QUEUE-'].update(values=[])
                window['-FILE LIST-'].update(load_dir_files(opt['file_dir']))
                blank_window.close()
                file_window.close()
                table_window.close()
        if "Add -->" in event:
            if values['-FILE LIST-']:
                queue = window['-QUEUE-'].get_list_values()
                queue.extend(values['-FILE LIST-'])
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
        if "Run Queue" in event:
            if window['-QUEUE-'].get_list_values():
                test_queue = window['-QUEUE-'].get_list_values()
                opt['queue_running_flag'] = True
                with open(opt['queue_file_name'], 'w') as selected_test_queue_file:
                    yaml.dump(test_queue, selected_test_queue_file)
                logger.debug('{}'.format('\n'.join(test_queue)))
                run_scripts = True
                break
        if "Modify Queue" in event:
            test_queue = window['-QUEUE-'].get_list_values()
            with open(opt['queue_file_name'], 'w') as selected_test_queue_file:
                yaml.dump(test_queue, selected_test_queue_file)
            logger.debug('{}'.format('\n'.join(test_queue)))

    # before exiting the program make sure all the windows are closed
    blank_window.close()
    table_window.close()
    file_window.close()
    window.close()
    return run_scripts


# Generation of PC metadata
# ------------------------------------------------------------------------------
def create_station_config(config_file_name='.station_config.yaml'):

    if Path(config_file_name).is_file():
        # config file already exists
        logger.debug(f'Config file exists: {config_file_name}')
        return config_file_name

    config_file = None

    sg.popup('No station config file exists in directory\n'
             'Please enter the details to create the Test Station')

    layout = [[sg.Text('Test Station Data')],
              [sg.Text('ID number:', size=(12, 1)), sg.InputText(key="station_id")],
              [sg.Text('Country location:', size=(12, 1)), sg.InputText(key="country")],
              [sg.Text('City location:', size=(12, 1)), sg.InputText(key="city")],
              [sg.Text('Description:', size=(12, 1)), sg.InputText(key="description")],
              [sg.Text('Script directory:', size=(12, 1)), sg.InputText(key="script_dir", default_text=Path.cwd()),
               sg.FolderBrowse(button_text='...', target='script_dir', initial_folder=Path.cwd())],

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
            with open('.station_config.yaml', 'w') as f:
                yaml.dump(values, f)
            config_file = config_file_name
            break
    window.close()

    return config_file


# Main Script
# ------------------------------------------------------------------------------
def run_queue():

    try:
        os.remove(f"{opt['file_dir']}/stop.txt")
        logger.debug('File: \'stop.txt\' removed. Clear to run test.')
    except FileNotFoundError:
        logger.debug('File: \'stop.txt\' not found. Clear to run test.')

    test_count = 1

    while test_count > 0:

        test_queue = read_queue(opt['queue_file_name'])
        if test_queue is None:
            logger.debug(f'File: \'selected_test_queue.txt\' not found.')
            raise
        elif not test_queue:
            logger.debug(f'File: \'selected_test_queue.txt\' is blank.')
            return

        test_count = len(test_queue)
        logger.debug(f'Test Count: {test_count}')

        try:
            queue_file_out = ''
            if test_count > 0:
                queue_file_out = (test_queue[1:])
            else:
                queue_file_out = ('')
            with open(opt['queue_file_name'], 'w') as fd:
                yaml.dump(queue_file_out, fd)
        except Exception as ex:
            logger.exception(f'Unexpected error: {ex}')
            return

        if not os.path.exists(f"{opt['file_dir']}/stop.txt"):
            try:
                setup_csv_file_name = test_queue[0]
                logger.debug(setup_csv_file_name)
                logger.debug(f"Running: {opt['file_dir']}")
                time.sleep(20)
                #subprocess.run(['python', 'tcm.py', setup_csv_file_name], cwd=opt['file_dir'])
            except Exception as ex:
                logger.exception(f'Unexpected error: {ex}')
        else:
            logger.debug(f"{opt['file_dir']}/stop.txt Found")
            return True


# Finalize the script
# ------------------------------------------------------------------------------
def wrap_up(exit_state):
    if not exit_state:
        test_queue = read_queue(opt['queue_file_name'])
        if test_queue is None:
            logger.warning(f"Something went wrong. {opt['queue_file_name']} is missing")
            sg.popup(f"Something went wrong. {opt['queue_file_name']} is missing")
        # elif '@close' in test_queue:
        #     logger.info("No Tests Selected")
        elif test_queue:
            opt['previous_queue_list'] = test_queue
            sg.popup(f"Something went wrong. Storing the queue")

    try:
        os.remove(opt['queue_file_name'])
        logger.debug(f"\'{opt['queue_file_name']}\' file removed")
    except FileNotFoundError:
        logger.error(f"Something went wrong. {opt['queue_file_name']} is missing")
        sg.popup(f"Something went wrong. {opt['queue_file_name']} is missing")
    else:
        opt['queue_running_flag'] = False
        sg.popup('Session finished\n')

# Main Script
# ------------------------------------------------------------------------------
def run_queue_app():
    pretty_dict(opt)
    sg.theme(opt['theme'])

    # find a station configuration, otherwise create one. if user cancels exit the program.
    opt['station_config_file'] = create_station_config()
    if opt['station_config_file'] is None:
        logger.debug('User cancelled station config creation')
        return

    # open the main application, returns True if the user has hit the run button
    run = queue_window(opt['station_config_file'], opt['queue_running_flag'])

    successful_exit = False
    # only run the files if the user has hit the run button.
    if run:
        try:
            # the exit will only be successful if all of the scripts ran without stopping early.
            successful_exit = run_queue()
        except Exception as ex:
            logger.exception(ex)
        finally:
            wrap_up(successful_exit)

    logger.debug(opt)
    with open(opt_fn, 'w') as fd:
        yaml.dump(opt, fd)

