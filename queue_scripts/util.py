
import os
import argparse

from loguru import logger

from configure_logger import setup_logging
from queue_scripts_app import run_queue_scripts

__version__ = '0.1.0-dev1'

dev_debug = True # make False before releasing code

if __name__ == "__main__":

    """
    Docs
    """
    parser = argparse.ArgumentParser(prog='queue-scripts.py', description='GUI for creating a test sequence of python scripts to run.')
    parser.add_argument('--debug', action='store_true', help='Overwrite config and enable logger debugging.')
    parser.add_argument('--version', action='version', version=__version__, help='')

    args = parser.parse_args()

    setup_logging({'log_console_level': ('INFO', 'DEBUG')[args.debug or dev_debug]})  # basic setup script and doesn't require logging to a file
    logger.debug(f'Option Settings: {args}')
    try:
        run_queue_scripts()
    except KeyboardInterrupt:
        logger.warning('Keyboard Interrupt from user')
    except Exception as ex:
        if args.debug or dev_debug:
            logger.exception(ex)
        else:
            logger.error(f'Fatal error!\n\nTest sequence generator crashed.\n\nReason: {str(ex)}')