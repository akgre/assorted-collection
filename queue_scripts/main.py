"""
GUI for creating a test sequence of python scripts to run.
"""

import os
import platform

from loguru import logger

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from ez_logger import setup_logging
from queue_scripts_app import run_queue_app

module_name = "queue scripts"
__version__ = '0.1.0-dev1'

dev_debug = True  # make False before releasing code


def queue_scripts_main():
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

    # parser = ArgumentParser(prog='queue-scripts.py', description='')


    args = parser.parse_args()

    setup_logging(user_input=args.user, project_name='queue_scripts_dev')  # basic setup script and doesn't require logging to a file
    logger.debug(f'Option Settings: {args}')
    try:
        run_queue_app()
    except KeyboardInterrupt:
        logger.warning('Keyboard Interrupt from user')
    except Exception as ex:
        if args.verbose or dev_debug:
            logger.exception(ex)
        else:
            logger.error(f'Fatal error!\n\nTest sequence generator crashed.\n\nReason: {str(ex)}')


if __name__ == "__main__":
    queue_scripts_main()

