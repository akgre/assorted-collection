# ! /usr/bin/env python3

"""
ez_loguru: basic GUI setup for loguru in you projects

This module is the main setup. You can either copy this file into your project or import if you have installed it.
"""
import sys
import yaml
import datetime
import platform
import PySimpleGUI as sg
from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from loguru import logger

module_name = "ez_loguru: basic GUI setup for loguru in you projects"
__version__ = "0.1.0-dev1"


# Load global options dictionary from file
# ------------------------------------------------------------------------------
logging_options_fn = 'logging_options.yaml'
logging_options = {'log_records_dir': '{cwd}\LOGS\{project_name}',
                   'quiet_console': False,
                   'console_level': 'INFO',
                   'enable_console_file': False,
                   'console_file_name': '{datetime}_{project_name}_console.log',
                   'enable_verbose_file': False,
                   'verbose_level': 'DEBUG',
                   'verbose_file_name': '{datetime}_{project_name}_debug.log',
                   'file_rotation': '100 MB',
                   }

try:
    with open(logging_options_fn) as f:
        logging_options.update(yaml.load(f, Loader=yaml.FullLoader))
except FileNotFoundError:
    logger.debug(f'"{logging_options_fn}" not found. Default options loaded')


# GUI interface selection for setting up logging
# ------------------------------------------------------------------------------
def get_user_input_gui():

    submit_flag = False

    log_records_dir = logging_options['log_records_dir']
    log_records_dir_browse = (Path.cwd(), log_records_dir)[Path(log_records_dir).is_dir()]
    quiet_console = logging_options['quiet_console']
    console_level = logging_options['console_level']
    enable_console_file = logging_options['enable_console_file']
    console_file_name = logging_options['console_file_name']
    enable_verbose_file = logging_options['enable_verbose_file']
    verbose_level = logging_options['verbose_level']
    verbose_file_name = logging_options['verbose_file_name']

    layout = [[sg.Text('Quiet Console:', size=(14, 1)), sg.Check(text='', default=quiet_console, key='-CONSOLE LOGGING-', pad=(2, 1)),
               sg.Text('Will not display in the console. Will still output in console log if enabled')],
              [sg.Text('Console Logging:', size=(14, 1)), sg.Check(text='', default=enable_console_file, key='-CONSOLE FILE-', pad=(2,1)),
               sg.Text('Level:'), sg.Combo(default_value=console_level, values=['DEBUG', 'INFO', 'WARNING', 'ERROR'], size=(10,0), key='-CONSOLE LEVEL-'),
               sg.Text('Console File Name:', size=(14, 1)), sg.InputText(key='-CONSOLE FILE NAME-', default_text=console_file_name)],
              [sg.Text('Verbose Logging:', size=(14, 1)), sg.Check(text='', default=enable_verbose_file, key='-VERBOSE FILE-', pad=(2, 1)),
               sg.Text('Level:'), sg.Combo(default_value=verbose_level, values=['DEBUG', 'INFO', 'WARNING', 'ERROR'], size=(10,0), key='-VERBOSE LEVEL-'),
               sg.Text('Verbose File Name:', size=(14, 1)), sg.InputText(key='-VERBOSE NAME-', default_text=verbose_file_name)],
              [sg.Text('Log File Directory:', size=(14, 1)), sg.InputText(key='-lOG DIR-', default_text=log_records_dir, size=(84, 0)),
               sg.FolderBrowse(button_text='...', target='-lOG DIR-', initial_folder=log_records_dir_browse, pad=(1, 0))],

              [sg.Submit(), sg.Cancel()]]

    window = sg.Window('Setup Logging', layout)

    while True:
        event, values = window.read()
        # End program if user closes window or
        # presses the Cancel button
        if event == "Cancel" or event == sg.WIN_CLOSED:
            break
        if "Submit" in event:
            logging_options['log_records_dir'] = values['-lOG DIR-']
            logging_options['quiet_console'] = values['-CONSOLE LOGGING-']
            logging_options['console_level'] = values['-CONSOLE LEVEL-']
            logging_options['enable_console_file'] = values['-CONSOLE FILE-']
            logging_options['console_file_name'] = values['-CONSOLE FILE NAME-']
            logging_options['enable_verbose_file'] = values['-VERBOSE FILE-']
            logging_options['verbose_level'] = values['-VERBOSE LEVEL-']
            logging_options['verbose_file_name'] = values['-VERBOSE NAME-']
            with open(logging_options_fn, 'w') as f:
                yaml.dump(logging_options, f)
            submit_flag = True
            break
    window.close()

    return submit_flag


# Main logging setup. loads the options then creates the loggers.
# ------------------------------------------------------------------------------
def setup_logging(user_input=False, log_records_dir=None, quiet_console=None, console_level=None,
                  enable_console_file=None, console_file_name=None, enable_verbose_file=None, verbose_level=None,
                  verbose_file_name=None, file_rotation=None, project_name=''):

    if log_records_dir is not None:
        logging_options['log_records_dir'] = log_records_dir
    if quiet_console is not None:
        logging_options['quiet_console'] = quiet_console
    if console_level is not None:
        logging_options['console_level'] = console_level
    if enable_console_file is not None:
        logging_options['enable_console_file'] = enable_console_file
    if console_file_name is not None:
        logging_options['console_file_name'] = console_file_name
    if enable_verbose_file is not None:
        logging_options['enable_verbose_file'] = enable_verbose_file
    if verbose_level is not None:
        logging_options['verbose_level'] = verbose_level
    if verbose_file_name is not None:
        logging_options['verbose_file_name'] = verbose_file_name
    if file_rotation is not None:
        logging_options['file_rotation'] = file_rotation

    first_time_setup = False
    if not Path(logging_options_fn).is_file():
        first_time_setup = True
        with open(logging_options_fn, 'w') as f:
            yaml.dump(logging_options, f)

    if user_input or first_time_setup:
        if get_user_input_gui() is None:
            return False

    log_records_dir = logging_options['log_records_dir']
    quiet_console = logging_options['quiet_console']
    console_level = logging_options['console_level']
    enable_console_file = logging_options['enable_console_file']
    console_file_name = logging_options['console_file_name']
    enable_verbose_file = logging_options['enable_verbose_file']
    verbose_level = logging_options['verbose_level']
    verbose_file_name = logging_options['verbose_file_name']
    file_rotation = logging_options['file_rotation']

    # format directory
    log_records_dir = log_records_dir.format(cwd=Path().cwd(), project_name=project_name)
    Path(log_records_dir).mkdir(parents=True, exist_ok=True)
    # format file names
    console_file_name = console_file_name.format(datetime=datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S"),
                                                     project_name=project_name)
    verbose_file_name = verbose_file_name.format(datetime=datetime.datetime.now().strftime("%y-%m-%d_%H-%M-%S"),
                                                     project_name=project_name)

    if not quiet_console:
        if 'INFO' in console_level:
            logger.add(sys.stderr, level=console_level)
            config = {
                "handlers": [
                    {"sink": sys.stdout, "format": "<level>{message:80}</level>",
                     'level': console_level},
                ]
            }
            logger.configure(**config)
        else:
            logger.add(sys.stderr, level=console_level)
            config = {
                "handlers": [
                    {"sink": sys.stdout, "format": "<level>{message:80}</level> | "
                                                   "<green>{time:YY-MM-DD HH:mm:SSS}</green> | "
                                                   "<level>{level:<8}</level> | "
                                                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>",
                     'level': console_level},
                ]
            }
            logger.configure(**config)
        logger.debug('Set up console logging')
    else:
        logger.remove()


    if enable_console_file:
        console_file_path = Path(log_records_dir, console_file_name)
        logger.add(console_file_path, format="{message: <80}", level=console_level, rotation=file_rotation)
        # logger.add(console_file_name, format="{message: <80} | "
        #                                     "{time:YY-MM-DD HH:mm:ss.SSS} | "
        #                                     "{level: <8} | "
        #                                     "{name}:{function}:{line}", level=setup['log_console_level'])
        logger.debug('Set up console logging to file')

    if enable_verbose_file:
        verbose_file_path = Path(log_records_dir, verbose_file_name)
        logger.add(verbose_file_path, format="{time:YY-MM-DD HH:mm:ss.SSS} | "
                                        "{level: <8} | "
                                        "{name}:{function:}:{line:} | "
                                        "{message}", level=verbose_level, rotation=file_rotation)
        logger.debug('Set up file logging')

    return True


# Main. For testing the logging setup
# ------------------------------------------------------------------------------
def ez_logger_main():
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

    args = parser.parse_args()

    try:
        # if logging gui is cancelled then stop the script
        if not setup_logging(project_name='dev'):
            return
    except KeyboardInterrupt:
        logger.warning('Keyboard Interrupt from user')
    except Exception as ex:
        if args.verbose:
            logger.exception(ex)
        else:
            logger.error(f'Fatal error!\n\nTest sequence generator crashed.\n\nReason: {str(ex)}')

    logger.debug('debug')
    logger.info('info')
    logger.warning('warning')
    logger.error('error')
    logger.critical('critical')


if __name__ == "__main__":
    ez_logger_main()

