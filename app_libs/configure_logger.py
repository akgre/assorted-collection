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
    configure_logger.py
    ~~~~~~~~~~~

    This is a simple logging setup that allows you to log to the console and optionally to 2 files
    default: logs to the console
    console to file: logs everything that was displayed in the console to a file
    debug to file: logs all information to a file. This allows the user to easily debug
            the script if something went wrong but the user doesn't need to have this
            data crowding up the console.

    :copyright: 2018 by Aaron Greenyer
    :license: MIT, see COPYING for more details.
"""

import sys
from loguru import logger

class Formatter:

    def __init__(self):
        self.padding = 120
        #self.fmt = "{time:YY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line}{extra[padding]} | {message}\n{exception}"
        self.fmt = "<level>{message}{extra[padding]} </level> | <green>{time:YY-MM-DD HH:mm:SSS}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>\n"

    def format(self, record):
        length = len("{message}".format(**record))
        self.padding = max(self.padding, length)
        record["extra"]["padding"] = " " * (self.padding - length)
        return self.fmt

formatter = Formatter()


def setup_logging(logging_setup=None):
    '''
    :param logging_setup:
    :return:
    The user sends a dictionary setup:
        log_console_level: sets the level of the console
            if the level is INFO then then no extra string
            formatting is included. This is to prevent the
            console from looking crowded.

        test_logs_dir: the default location is to save the
            log files to the current working directory.
            Updating this with an absolute path will record
            the log files in that directory.

        log_console_file: If the has a name then the console
            logging will get recorded to this file as well.
            Note: The formatting will be included in the file.

        log_file_level: sets the level of the log file.
            default setting is DEBUG

        log_file_name: If the has a name then the logging
            (at the level set by log_file_level) will get
            recorded to this file as well.
            Note: The formatting will be included in the file.
    '''

    setup = {'log_console_level': 'INFO',
             'test_logs_dir': '',
             'log_console_file': None,
             'log_file_level': 'DEBUG',
             'log_file_name': None}
    if logging_setup is not None:
        setup.update(logging_setup)
    if setup['log_console_level'] is not None:
        if 'INFO' in setup['log_console_level']:
            logger.add(sys.stderr, level=setup['log_console_level'])
            handler_config = {
                "handlers": [
                    {"sink": sys.stdout, "format": "<level>{message:80}</level>",
                     'level': setup['log_console_level']},
                ]
            }
            logger.configure(**handler_config)
        else:
            logger.remove()
            logger.add(sys.stderr, format=formatter.format, level=setup['log_console_level'])
            #     handler_config = {
            #         "handlers": [
            #             {"sink": sys.stdout, "format": "<level>{message:160}</level> | "
            #                                            "<green>{time:YY-MM-DD HH:mm:SSS}</green> | "
            #                                            "<level>{level:<8}</level> | "
            #                                            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>",
            #              'level': setup['log_console_level']},
            #         ]
            #     }
            #     logger.configure(**handler_config)
            #
            #
            logger.debug('Set up console logging')

    test_logs_dir = (setup['test_logs_dir'], sys.path[0])[setup['test_logs_dir'] == '']
    if setup['log_console_file'] is not None:
        logger.debug(f'Console file save Location: {sys.path[0]}')
        console_file_name = f"{test_logs_dir}/{setup['log_console_file']}"
        logger.add(console_file_name, format=formatter.format, level=setup['log_console_level'], rotation="100 MB")
        logger.debug('Set up console logging to file')
    else:
        logger.debug('No console file setup')

    if setup['log_file_name'] is not None:
        logger.debug(f'Debug file save Location: {sys.path[0]}')
        filename = f"{test_logs_dir}/{setup['log_file_name']}"
        logger.add(filename, format=formatter.format, level=setup['log_file_level'], rotation="100 MB")
        logger.debug('Set up file logging')
    else:
        logger.debug('No debug file setup')


def test_setup_logging():
    setup_example = {'log_console_level': 'DEBUG',
                     'test_logs_dir': '',
                     'log_console_file': 'copy_of_console',
                     'log_file_level': 'DEBUG',
                     'log_file_name': 'log_to_file'}
    setup_logging(setup_example)
    logger.debug('debug')
    logger.info('info')
    logger.warning('warning')
    logger.error('error')
    logger.critical('critical')
