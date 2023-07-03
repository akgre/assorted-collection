from __future__ import annotations

import csv
import re
from decimal import Decimal
from typing import Optional, List, Literal, Union
from uuid import UUID

from pydantic import BaseModel, constr, conint, validator, root_validator, ValidationError, Field, Extra
from pydantic.error_wrappers import ErrorWrapper

from src.drwats.wats_steps import Step
from src.drwats.wats_enums import ReportType, ResultStatus


class UUTReport305(BaseModel, extra=Extra.allow):
    PartNumber: constr(min_length=1, max_length=100)
    ProjectName: Optional[constr(min_length=1, max_length=100)]
    ItemName: Optional[constr(min_length=1, max_length=100)]
    Batch: Optional[constr(min_length=1, max_length=100)]
    Revision: Optional[constr(min_length=1, max_length=100)]
    SerialNumber: Optional[constr(min_length=1, max_length=100)]
    Site: conint(gt=0, lt=9999)
    PONo: Optional[constr(min_length=1, max_length=100)]
    EAN: Optional[constr(min_length=1, max_length=100)]
    UPC: Optional[constr(min_length=1, max_length=100)]
    FWVer: Optional[constr(min_length=1, max_length=100)]
    FWVers: Optional[constr(min_length=1, max_length=100)]
    # SWFileName: Optional[constr(min_length=1, max_length=100)]
    SWVersion: Optional[constr(min_length=1, max_length=100)]
    DateTime: constr(regex=r'\d{2,4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}', max_length=19)
    UTCOffset: conint(ge=-14, le=14)
    Operator: Optional[constr(min_length=1, max_length=100)]
    StationName: constr(min_length=1, max_length=100)
    StationType: conint(gt=0, lt=9999)
    ProtocolVersion: Optional[constr(min_length=1, max_length=100)]
    TestSocket: Optional[constr(min_length=1, max_length=100)]
    ExecutionTime: Optional[constr(min_length=1, max_length=100)]
    TestComment: Optional[constr(min_length=1, max_length=4000)]
    Result: Optional[constr(min_length=1, max_length=100)]
    Misc_SpecVersion: Optional[constr(min_length=1, max_length=100)]
    Misc_BDADDR: Optional[constr(min_length=1, max_length=100)]
    SUB_DEVICEID: Optional[constr(min_length=1, max_length=100)]

    @root_validator(pre=True)
    def validate_attribute_names(cls, values):

        max_len = max([len(name) for name in values.keys()])
        for attribute_name, attribute_value in values.items():
            print(f"{attribute_name + ' ':_<{max_len}} = {attribute_value}")

        errors = []
        for attribute_name, attribute_value in values.items():

            if "SUB" in attribute_name or "MISC" in attribute_name.upper():
                name = re.search(r'^[SUB|Sub|sub|MISC|Misc|misc]+_[A-Za-z\d]{1,20}$', attribute_name)
                if not name:
                    errors += [ErrorWrapper(
                        ValueError(f'Field name: {attribute_name} does not meet the expression requirements'),
                        loc=(attribute_name,))]
                if len(attribute_value) > 100:
                    errors += [ErrorWrapper(
                        ValueError(f'{attribute_name}: has a value that is too long.'),
                        loc=(attribute_name,))]
                continue

            elif "(" in attribute_name or ")" in attribute_name:

                # fist check that the name meets a generic condition

                if any([name_type in attribute_name for name_type in
                        ['(Sec_Time)', '(Eval)', '(File)', '(Comment)', '(Image)']]):
                    # if sec time then number

                    # if eval then 0, 1, 2 (2 is an auto eval feature)

                    # if file, comment, image then expect string

                    if values[attribute_name] is None:
                        print(f'{attribute_name} is missing a value')
                    continue

                elif any([name_type in attribute_name for name_type in
                          ['(ResponseLog)', '(ResponseLin)', '(ResponseLinLog)', '(ResponseLogLog)']]):

                    # the regex for graph is always the same
                    if values[attribute_name] is None:
                        print(f'{attribute_name} is missing a value')
                    continue

                else:
                    name = re.search(r'^.*\(.*~.* .*\)$', attribute_name)
                    if name is None:
                        errors += [ErrorWrapper(
                            ValueError(f'Field name: {attribute_name} does not meet the expression requirements'),
                            loc=(attribute_name,))]
                        continue

                    # check if test is a bool

                    # check if test is hex

                    # otherwise test will be a numeric value.
                    if attribute_value is None:
                        print(f'{attribute_name} is missing a value')

                continue

            elif attribute_name in UUTReport305.__fields__.keys():
                if values[attribute_name] is None:
                    print(f'{attribute_name} is missing a value')
                continue
            # elif 'Unnamed' in attribute_name:
            #     ...
            else:
                print(f"{attribute_name}")
                errors += [ErrorWrapper(
                    ValueError(f'Field name: {attribute_name} does not meet the expression requirements'),
                    loc=(attribute_name,))]
        if errors:
            raise ValidationError(errors, model=cls)
        return values


"""
PartNumber:
ProjectName:
ItemName:
Revision:
Batch:
SerialNumber:
Site:
PONo:
EAN:
UPC:
FWVer:
FWVers:
SWVersion:
DateTime:
UTCOffset:
Operator:
StationName:
StationType:
ProtocolVersion:
TestSocket:
ExecutionTime:
TestComment:
Result:
Misc_SpecVersion:
Misc_BDADDR:
SUB_DEVICEID:
TestComment:
"""


def detect_csv_delimiter(file):
    with open(file) as detect_csv_file:
        try:
            start = detect_csv_file.read(4096)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(start)
            print("dialect", dialect.delimiter)
        except Exception as ex:
            print(ex)
            print("Could not get a csv dialect -> probably not a csv")
            return None
    return dialect.delimiter


def check_csv_table(file, file_delimiter):
    with open(file) as detect_csv_file:
        csv_reader = [row for row in csv.reader(detect_csv_file, delimiter=file_delimiter)]

    header_len = len(csv_reader[0])
    if any([cell == "" for cell in csv_reader[0]]):
        for _count, cell in enumerate(csv_reader[0]):
            if cell == "":
                print(f'Error: Header cell {_count + 1} is empty')

        return None

    line_errors = []
    for line_count, row in enumerate(csv_reader, start=1):
        if r'\n' in repr(",".join(row)):
            print(repr(",".join(row)))
            for _count, cell in enumerate(row):
                if r'\n' in repr(cell):
                    line_errors.append([line_count, f'Error: Cell {_count + 1} contains a new line character'])
        if len(row) != header_len:
            line_errors.append(
                [line_count, f'Error: Line {line_count} had {len(row)} columns when there should be {header_len}'])
    for error in line_errors:
        print(error)
        raise IOError
    print(f'Processed {line_count} lines')
    return True


# import PySimpleGUI as sg
#
#
# def create_layout():
#     return [[sg.Text("Report File:"), sg.Input(), sg.FileBrowse(), sg.Text("Line Number:"),
#              sg.Spin(list(range(100)), s=(15, 2))],
#             [sg.Column([[sg.Text("Data Log")], [sg.Multiline(size=(80, 15), key="-DASHBOARD_TEXTBOX-")],
#                         [sg.Text("WATS Report")], [sg.Multiline(size=(80, 15), key="-DASHBOARD_TEXTBOX2-")]]),
#              sg.Column([[sg.Text("Error List")], [sg.Multiline(size=(60, 32), key="-DASHBOARD_TEXTBOX2-")]])]]
#
#
# layout = [[create_layout()],
#           [sg.Button("Validate"), sg.Button("Refresh"), sg.Cancel()]
#           ]
#
# window = sg.Window('Dr WATS', layout)
#
# while True:
#     event, values = window.read()
#     if event == sg.WIN_CLOSED or event == 'Cancel':
#         break
#
#     if event == 'Validate':
#         def extract_keys(data):
#             keys = []
#             for key, value in data.items():
#                 keys.append((key,))
#                 if isinstance(value, dict):
#                     keys += [(key,) + subkey for subkey in extract_keys(value)]
#                 elif isinstance(value, list):
#                     for i, element in enumerate(value):
#                         keys += [(key, i) + subkey for subkey in extract_keys(element)]
#
#             return keys
#
#
#         json_loc = extract_keys(json.loads(json_file))
#         line_list_json = list(json.dumps(json.loads(json_file), indent=4).split("\n"))
#         complete_list = []
#         for i, x in enumerate(line_list_json):
#             if ":" in x:
#                 print((i, json_loc[0], x))
#                 complete_list.append((i, json_loc.pop(0), x))
#             else:
#                 complete_list.append((i, "", x))
#         for y in complete_list:
#
#             if y[1] in e_loc:
#                 print(y[1], e_loc)
#                 window["-DASHBOARD_TEXTBOX-"].print(y[2], background_color='yellow')
#                 window["-DASHBOARD_TEXTBOX2-"].print(message_dict[y[1]])
#
#             else:
#                 window["-DASHBOARD_TEXTBOX-"].print(y[2])
#
# window.close()

report = {
    "PartNumber": "abc",
    "ProjectName": "project",
    "ItemName": "project",
    "Revision": "8",
    "Batch": "batch",
    "SerialNumber": "123",
    "Site": 1200,
    "PONo": "po",
    "EAN": "ean",
    "UPC": "upc",
    "FWVer": "fwver",
    "FWVers": "fwvers",
    "SWVersion": "swv",
    "DateTime": "22-12-12 10:10",
    "UTCOffset": "+4",
    "Operator": "jan",
    "StationName": "station",
    "StationType": 2,
    "ProtocolVersion": 4,
    "TestSocket": -1,
    "ExecutionTime": 12.12,
    "TestComment": "comment",
    "Result": 1,
    "Misc_SpecVersion": "1.1.1",
    "Misc_BDADDR": "GEGE",
    "SUB_DEVICEID": "1234",
    "3.6f_BT_Sens[TP100](100~150 RSSI": "123",
    "bob": "fefe2"
}

try:
    m = UUTReport305(**report)
    print(m.json(indent=2))
except ValidationError as e:
    from types import SimpleNamespace

    for error in [SimpleNamespace(**error) for error in e.errors()]:
        print(f"{error.type:<28} | {str(error.loc):<36} | {error.msg}")

delimiter = detect_csv_delimiter('305.csv')
if not check_csv_table('305.csv', delimiter):
    exit()
reader = csv.DictReader(open('305.csv'), delimiter=delimiter)

report = next(reader)

try:
    m = UUTReport305(**report)
    print(m.json(indent=2))
except ValidationError as e:
    from types import SimpleNamespace

    for error in [SimpleNamespace(**error) for error in e.errors()]:
        print(f"{error.type:<28} | {str(error.loc):<36} | {error.msg}")

# with open('305.csv', 'w') as f:
#     w = csv.DictWriter(f, m.dict().keys(), delimiter=";")
#     w.writeheader()
#     w.writerow(m.dict())


# def convert_305_to_dict(data_305):
#
#     main_header_305 = {}
#     sub_info = []
#     misc_info = []
#     step_data_order = []
#     step_data_groups = {}
#
#     for key_305 in data_305.keys():
#         if key_305 in UUTReport305.__fields__.keys():
#             main_header_305[key_305] = js[key_305]
#
#         elif "SUB_" in key_305.upper():
#             sub_key = key_305[4:]
#             sub_info.append({'partType': sub_key, 'sn': js[key_305]})
#
#         elif "SUB_" in key_305.upper():
#             sub_key = key_305[5:]
#             sub_info.append({'description': sub_key, 'text': js[key_305]})
#
#         elif "(" in key_305:
#             data_key = key_305.split("(")[0]
#             if data_key not in step_data_order:
#                 step_data_order.append(data_key)
#                 step_data_groups[data_key] = {}
#             step_data_groups[data_key].update(key_305: js[key_305])
#
#         else:
#             misc_info.append({'description': key_305, 'text': js[key_305]})


from pydantic.error_wrappers import ErrorWrapper
from pydantic.errors import PydanticValueError


# class MyError(ErrorWrapper):
#     code: str
#     message: str
#     loc: tuple
#
#     def __init__(self, *, message: str, loc: tuple):
#         super().__init__(exe=message, loc=loc)


class MyModel(BaseModel):
    value: int

    @root_validator()
    def value_must_be_greater_than_zero(cls, values):
        if values['value'] < 0:
            raise ValidationError([ErrorWrapper(ValueError('domain already exists'),
                                                loc=("domain", "bob"))], model=cls)
        return values


try:
    m = MyModel(value=-2)
    print(m.json(indent=2))
except ValidationError as exc_info:
    """
    WHAT: if the value is invalid, the script will catch the ValidationError exception and iterate through the 
    raw_errors list to modify the _loc attribute of each error. 

    Specifically, the raw_error._loc attribute is updated with a new tuple that excludes the '__root__' element. The 
    loc_tuple() attribute returns a tuple containing the location of the validation error in the data structure, 
    and __root__ refers to the top-level element of the data structure. By excluding this element, the new tuple 
    contains the location of the validation error within the data structure, relative to the top-level element. 

    The modified _loc attribute will then be used to display a more informative error message that specifies the 
    location of the error within the data structure. 
    
    WHY: sometimes in the root_validator there will be an evaluation of multiple field values and when the error is 
    raised from the root_validator the error location will contain __root__ as the last element. This of course is 
    not a valid field so we can modify the error location to have the field that best fits the error that was raised; 
    and for this we need to remove the __root__ from the location.
    """
    import json

    error_list = json.loads(exc_info.json())
    print(json.loads(exc_info.json()))
    for error in error_list:
        error['loc'] = tuple([loc for loc in error['loc'] if loc != '__root__'])
    print(error_list)
