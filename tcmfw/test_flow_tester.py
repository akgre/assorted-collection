import os
import json
import time
import random
import string
import prettytable

from loguru import logger
from configure_logger import setup_logging

setup_logging({'log_console_level': 'INFO'})

def word():
    return ''.join(random.choice(string.ascii_lowercase) for i in range(10))
def number(max_val=1000):
    return random.randint(0, max_val)
def make_table(num_rows, num_cols):
    data = [[j for j in range(num_cols)] for i in range(num_rows)]
    #data[0] = [word() for __ in range(num_cols)]
    for i in range(0, num_rows):
        data[i] = ['', f'Test_{i:03}', word(), '', '', '']##word(), *[number() for i in range(num_cols - 2)]]
    return data

def pretty_table(t):
    pretty=prettytable.PrettyTable()
    for i in t:
        pretty.add_row(i)
    print(pretty)

def pretty_dict(d, indent=0):
    for key, value in d.items():
        logger.info('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty_dict(value, indent+1)
        else:
            logger.info('\t' * (indent+1) + str(value))

def shutdown():
    exit()

with open('tcm_data2.json') as f:
    tcm_data = json.load(f)

pretty_dict(tcm_data)

tcm_data['test_case_files']['test_case_history'] = []
tcm_data['test_brief']['test_definition_list'] = []


table_data = make_table(num_rows=10, num_cols=5)

tcm_data['test_brief']['test_definition_list'] = table_data

pretty_table(table_data)

tcm_data['test_case_files']['test_case_history'] = []

#logger.info(table_data)

for x in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l']:
    table_data = make_table(num_rows=10, num_cols=5)
    tcm_data['test_case_files']['current_test_case'] = x
    tcm_data['test_brief']['test_definition_list'] = table_data
    for current_test in table_data:
        for current_test_clear_icon in table_data:
            current_test_clear_icon[0] = ''
        current_test[0] = '▶'
        print(current_test)
        pretty_table(table_data)
        tcm_data['test_brief']['test_definition_list'] = table_data
        values = tcm_data
        with open('tcm_data.json', 'w') as f:
            json.dump(values, f, indent=2)
        if os.path.exists('stop.txt'):
            with open('stop.txt', 'r') as f:
                file = f.read()
            if 'stop' in file:
                os.remove('stop.txt')
                shutdown()
        time.sleep(1)
        current_test[3] = number()
        current_test[4] = ('Fail', 'Pass')[current_test[3] > 50]
        with open('tcm_data.json', 'w') as f:
            json.dump(values, f, indent=2)

    tcm_data['test_case_files']['test_case_history'].append(x)
    logger.info(tcm_data['test_case_files']['test_case_history'])
    values = tcm_data

    with open('tcm_data.json', 'w') as f:
        json.dump(values, f, indent=2)

