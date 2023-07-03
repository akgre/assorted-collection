from __future__ import annotations

import datetime
import uuid
from decimal import Decimal
from typing import List, Literal
from uuid import UUID
# import requests
import json

from pydantic import BaseModel, validator, root_validator, ValidationError, Field, PydanticValueError
from pydantic.error_wrappers import ErrorWrapper

from src.drwats.wats_steps import Step
from src.drwats.wats_enums import ReportType, ResultStatus, AdditionalDataTypes


class AssetInfo(BaseModel):
    assetSN: str = Field(..., min_length=1, max_length=100,
                         title='SerialNumber',
                         description='The asset serial number that is set in WATS')
    usageCount: int = Field(..., gt=0, lt=1000,
                            title='AssetCount',
                            description='counts how many times the unit has been used')


class SubUnits(BaseModel):
    """
    You can attach subunits to the test report, which will be linked in the report header. This allows
    you track systems and their individual component, which gives traceability to the systems lifecycle
    """
    partType: str = Field(..., min_length=1, max_length=50,
                          description='This is the same as part category in the WATS product manager')
    pn: str = Field(..., min_length=1, max_length=100)
    rev: str = Field(..., min_length=1, max_length=100)
    sn: str = Field(..., min_length=1, max_length=100)


class MiscInfos(BaseModel):
    description: str = Field(..., min_length=1, max_length=100, title='Miscellaneous Information',
                             description='Although this says descriptions it more appropriate to call it the '
                                         'name/key/field of the information')
    text: str = Field(None, min_length=1, max_length=100, title='Text',
                      description='String of the information. The documentation states this is optional if a numeric '
                                  'is supplied.')
    numeric: float = Field(None, ge=-2_147_483_648, le=2_147_483_647, title='Numeric',
                           description='Numeric of the information. The documentation states this is optional if a '
                                       'text is supplied.')

    @validator('numeric')
    def validate_numeric(cls, value, values):
        if value is None and values['text'] is None:
            raise ValueError(f'Either "text" or "numeric" require a value. text is optional if numeric is supplied '
                             f'and numeric is optional if text is supplied ')
        return value


class AdditionalDataProp(BaseModel):
    name: str = Field(..., title='Name', description='Sub name of additional data. The max length is not known')
    type: Literal[AdditionalDataTypes.tuple()] = Field(..., title='Type',
                                                       description='Value type of property')
    flags: int = Field(None, title='Flags', description='Bit flags of property. Unsure of use')
    value: str = Field(None, title='Value', description='Required for Number String, and Bool types, else Optional ('
                                                        'not included if null)')
    comment: str = Field(None, title='Comment', description='Comment of the property. Will not be displayed in a '
                                                            'report. The max length is not known')
    props: List[AdditionalDataProp] = Field(None, title='Properties', description='Array of AdditionalDataProperty '
                                                                                  'objects. type must be set to Obj')
    array: list = Field(None, title='Array', description='Array information. Used for type Array. I don\'t think '
                                                         'anyone will use this')


class AdditionalData(BaseModel):
    """
    You can add additional header data to the report. Additional data is a free-form structure of properties
    and values. If you use the name “Station info”, that additional data will be treated as additional station
    data.
    """
    name: str = Field(..., min_length=1, max_length=100, title='Name',
                      description='Root name of the additional data. Example displayed, root.stem.stem')
    props: List[AdditionalDataProp] = Field(..., title='Properties',
                                            description='The root of the array of properties for additional data')


class UUT(BaseModel):
    execTime: Decimal = Field(None, ge=0, title='Execution Time',
                              description='[OPTIONAL] The total time in second to complete the report. '
                                          'Although a negative value can be entered into the API the DrWATS '
                                          'model will only accept a value greater or equal to 0. Note: Limit '
                                          'is more than a googol (1×10^308)')
    testSocketIndex: int = Field(None, ge=-1, le=32767, title='Test Socket Index',
                                 description='[OPTIONAL] This indicates a socket ID if the test fixture is '
                                             'able to test multiple items at the same time. The user '
                                             'decides if the indexing starts at 1 or 0. The value -1 '
                                             'represents that there is only one test socket. Anything lower '
                                             'than -1 will be shown but in the report does not have a '
                                             'meaning and the model will reject.')
    batchSN: str = Field(None, max_length=100, title='Batch Serial Number',
                         description='[OPTIONAL] In electronics manufacturing, a batch serial number is a unique '
                                     'identifier assigned to a group of products that were manufactured together. It '
                                     'helps to track and identify specific products from a particular batch in case '
                                     'of any issues or defects. The format of a batch serial number may vary '
                                     'depending on the manufacturer and the type of product being produced. However, '
                                     'it typically includes a combination of letters, numbers, and special characters '
                                     'that represent specific information about the product batch, such as the '
                                     'manufacturing date, production location, and batch size. Example: PNB-291720-01 '
                                     'Note: will take 100 charaters but any more than 33 will go past the allocated'
                                     'space on the web page.')
    comment: str = Field(None, max_length=5000, title='Report Comment',
                         description='Can be any text up to 5000 charters.')
    errorCode: int = Field(None, ge=-2_147_483_648, le=2_147_483_647, title='Error Code',
                           description='The error code will only display in the report if there is also an '
                                       'error message. The error code is is up to the user to define, '
                                       'although this is based on NI error messages.'
                                       'NI has a set of error codes that are used to indicate specific '
                                       'errors or issues that may occur. These error codes consist of a '
                                       'numerical value and an associated error message that provides more '
                                       'information about the error. The error codes and messages are '
                                       'documented in the product manuals and online resources provided by '
                                       'NI. '
                                       'In general, error codes can be positive, negative, or zero (which '
                                       'is usually assigned to success). In the case of National '
                                       'Instruments error codes, negative error codes are used to indicate '
                                       'errors that are related to system or hardware issues, '
                                       'while positive error codes are used to indicate errors that are '
                                       'related to software issues. For example, negative error codes in '
                                       'the range of -200000 to -200999 are reserved for errors related to '
                                       'hardware or system issues such as incorrect configuration, '
                                       'connection issues, or hardware failure. On the other hand, '
                                       'positive error codes in the range of 1 to 99999 are reserved for '
                                       'errors related to software issues such as invalid arguments, '
                                       'incorrect usage of functions or APIs, or internal errors in the '
                                       'software. However, it\'s important to note that this is just a '
                                       'general convention, and different systems or software may use error '
                                       'codes differently. It\'s always best to refer to the specific '
                                       'documentation for the system or software in question to understand '
                                       'the meaning and usage of error codes.')
    errorMessage: str = Field(None, max_length=200, title='Error Message',
                              description='The corresponding message to the error code.'
                                          'Having an error message will display an icon, error code and message on '
                                          'the report. '
                                          'Although there isn\'t a limit to the string length it will only display on '
                                          'one line on the report. This is probably around 200 characters. To avoid '
                                          'this there must be new line characters.')
    fixtureId: str = Field(None, max_length=100, title='Fixture ID',
                           description='This is the ID number of the fixture the unit under test is placed on. '
                                       'If the fixture is also listed as an asset in the WATS asset manager then this'
                                       'will also need to be added to the asset list for the report. '
                                       'Even though the charter limit is 100, there will be a limit to how much of it '
                                       'can be displayed on screen in a report.')
    user: str = Field(..., min_length=1, max_length=100, title='User',
                      description='The user can either be set to a user type (admin, super user, operator), the name '
                                  'of the user or an ID of the user. This will be a decision for the '
                                  'test/system designers. '
                                  'Even though the charter limit is 100, there will be a limit to how much of it '
                                  'can be displayed on screen in a report')
    batchFailCount: int = Field(None, ge=0, le=2_147_483_647, title='Batch Fail Count',
                                description='In electronics manufacturing, a batch fail count is the number of failed '
                                            'products within a specific production batch or run. This count is often '
                                            'used to track the quality and reliability of a particular manufacturing '
                                            'process, as well as to identify areas where improvements can be made. '
                                            'The batch fail count is typically used by quality control teams to '
                                            'assess the overall performance of a production process. By tracking the '
                                            'number of failures over time, the team can identify patterns or trends '
                                            'that may indicate a problem with the process. For example, if the batch '
                                            'fail count increases over time, it may indicate that a particular '
                                            'component or process step is causing defects that need to be addressed. '
                                            'Overall, the batch fail count is an important metric for measuring the '
                                            'effectiveness of a manufacturing process, and can be used to drive '
                                            'continuous improvement efforts to ensure high quality and reliable '
                                            'products.')
    batchLoopIndex: int = Field(None, ge=0, le=2_147_483_647, title='Batch Loop Index',
                                description='This is part of NI\'s batch processing.')
    stepIdCausedUUTFailure: int = Field(None, ge=0, le=2_147_483_647, title='', exclude=True,
                                        description='The ID of the step that caused the report to fail. '
                                                    'This is an output only value from when you get the report from '
                                                    'WATS after it has been processed.')


class UUTReport(BaseModel):
    type: Literal[ReportType.tuple()] = Field(..., title='Type', description='The type of report, T = Test, R = Repair')
    id: UUID = Field(..., title='ID', description='A Globally Unique ID of the report. A report submitted with the '
                                                  'same ID as another will overwrite the report. For the client if '
                                                  'missing it will be generated but it must be supplied if uploaded '
                                                  'using the swagger API. The valid format for a GUID is '
                                                  '{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX} where X is a '
                                                  'hex digit (0,1,2,3,4,5,6,7,8,9,A,B,C,D,E,F).')
    pn: str = Field(..., min_length=1, max_length=100, title='Part Number')
    sn: str = Field(..., min_length=1, max_length=100, title='Serial Number')
    rev: str = Field(..., min_length=1, max_length=100, title='Revision')
    productName: str = Field(None, min_length=1, max_length=100)
    processCode: int = Field(..., ge=0, lt=32_767, title='Process Code',
                             description='The process code must first be created in WATS for it can be used. If not '
                                         'the API will reject the upload.')
    processCodeFormat: str = Field(None, min_length=1, max_length=100)
    processName: str = Field(None, min_length=1, max_length=100)
    result: Literal[ResultStatus.tuple()] = Field(..., title='Result',
                                                  description='The result of the whole report. This must match the '
                                                              'result of the first step in root.')
    machineName: str = Field(..., min_length=1, max_length=100, title='Station Name',
                             description='The identifier descided by the test/system designers of the station/PC '
                                         'where the test is performed. The documentation states it\'s an optional '
                                         'field, from testing this field is a requirement.')
    location: str = Field(..., min_length=1, max_length=100, title='Station Location',
                          description='This can be the city, post code, or any other identifier created for the '
                                      'location of the station. The documentation states it\'s an optional '
                                      'field, from testing this field is a requirement.')
    purpose: str = Field(..., min_length=1, max_length=100, title='Station Purpose',
                         description='A description of the purpose for the station. The documentation states it\'s an '
                                     'optional field, from testing this field is a requirement.')
    origin: str = Field(None, min_length=1, max_length=100, title='Origin', exclude=True,
                        description='This is an internal field for WATS and will only by displayed when getting a '
                                    'report. It must be set to null or removed before uploading the report. WATS adds '
                                    'the user\'s username as origin to the report if it is missing. When using the '
                                    'WATS Client API the client automatically sets origin as itself. Origin is used '
                                    'to tie the report to a client in system manager, for filtering and restricting '
                                    'access to reports.')
    start: str = Field(...,
                       regex=r'^(\d{2,4}-\d{1,2}-\d{1,2})(T\d{2}:\d{2}:\d{2}(\.\d{1,10})?(Z|[+-]\d{1,2}:?\d{2})?)?$',
                       # r'^\d{2,4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}.\d{1,2}.{0,10}\+\d{1,2}:\d{1,2}',
                       max_length=34, title='Local Start Time',
                       description='The minimum requirement for this field is the data in the format YYYYMMDD, however,'
                                   ' this model requires the full date time format. If the start date is in the '
                                   'future the report will not be processed unit that time has passed... but should '
                                   'we accept time travel in our testing?')
    startUTC: str = Field(None,
                          regex=r'^(\d{2,4}-\d{1,2}-\d{1,2})(T\d{2}:\d{2}:\d{2}(\.\d{1,10})?(Z|[+-]\d{1,2}:?\d{2})?)?$',
                          # r'^\d{2,4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}.\d{1,2}.{0,10}Z',
                          max_length=28, description='The UTC time must match the start time.')
    root: Step = Field(...)
    uut: UUT = Field(...)
    miscInfos: List[MiscInfos] = Field(None)
    subUnits: List[SubUnits] = Field(None)
    assets: List[AssetInfo] = Field(None)
    assetStats: list = []
    additionalData: List[AdditionalData] = Field(None)

    @validator('root')
    def validate_root(cls, value, values):
        print(value)
        if value.status != values['result']:
            raise ValidationError(
                [ErrorWrapper(ValueError(
                    f'Result ({values["result"]}) and first step status ({value.status}) must match'),
                    loc=("status",))], model=BaseModel)
        return value

    #
    @root_validator()
    def validate_report_rules(cls, report_values):
        print(report_values)
        missing = list(sorted(set(UUTReport.__fields__.keys()) - set(report_values.keys())))
        print(missing)
        if missing:
            raise ValidationError(
                [ErrorWrapper(ValueError(f'Unable to evaluate report with failed fields: {missing}'),
                              loc=("result",))], model=cls)
        # if report_values.get('root').status != report_values.get('result'):
        #     raise ValidationError(
        #         [ErrorWrapper(ValueError(
        #             f'Result ({report_values["result"]}) and first step status ({report_values["root"].status}) must '
        #             f'match'), loc=("result",))], model=BaseModel)
        return report_values


json_file = r"""
{
}
"""
"""
  "type": "T",
  "id": "35dfd5e5-8226-425f-822d-0da696e94",
  "pn": "OLC-140-C",
  "sn": "11506207",
  "rev": "8",
  "productName": null,
  "processCode": 1100,
  "processCodeFormat": null,
  "processName": "PCBA (demo)",
  "result": "F",
  "machineName": "wats-demo-01",
  "location": "skyWATS",
  "purpose": "demo",
  "origin": "00000000-0000-0000-0000-000000000000",
  "start": "2022-11-19T11:45:48.63+03:00",
  "startUTC": "2022-11-19T08:45:48.63Z",
  "root": {
    "id": 0,
    "group": "M",
    "stepType": "WATS_SeqCall",
    "name": "MainSequence Callback",
    "start": "2022-11-19T11:45:48.647+00:00",
    "status": "P",
    "errorCode": 0,
    "tsGuid": "ID#:AZur12wMdkuCxIdLZoEPbA",
    "totTime": 174.205173,
    "causedUUTFailure": false,
    "steps": [
      {
        "id": 1,
        "group": "M",
        "stepType": "WATS_SeqCall",
        "name": "Jig Power-up",
        "start": "2022-11-19T11:45:48.867+00:00",
        "status": "P",
        "errorCode": 0,
        "tsGuid": "ID#:v46JBTJoRECSUbOiswyrHD",
        "totTime": 5.1199504,
        "causedUUTFailure": false,
        "steps": [
          {
            "id": 2,
            "group": "M",
            "stepType": "Action",
            "name": "Apply Test Mode",
            "start": "2022-11-19T11:45:49+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:so0hMpGUkESNwBAtUhu5mA",
            "totTime": 0.0614246,
            "causedUUTFailure": false
          },
          {
            "id": 3,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:45:49.077+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:k5G2PNy3nUqQotJx5rbmXD",
            "totTime": 1.0037988,
            "causedUUTFailure": false
          },
          {
            "id": 4,
            "group": "M",
            "stepType": "Action",
            "name": "Init Chroma Power",
            "start": "2022-11-19T11:45:50.103+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:jyl/I96XDEWBwsae2AapNC",
            "totTime": 0.4723176,
            "causedUUTFailure": false
          },
          {
            "id": 5,
            "group": "M",
            "stepType": "Action",
            "name": "Turn Chroma Power ON",
            "start": "2022-11-19T11:45:50.597+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:XjHfo2a5rUClu9f/BXFpwD",
            "totTime": 0.1554111,
            "causedUUTFailure": false
          },
          {
            "id": 6,
            "group": "M",
            "stepType": "Action",
            "name": "UUT Power",
            "start": "2022-11-19T11:45:50.77+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:r2WxZQ9xi0G20co6juX50D",
            "totTime": 0.0197737,
            "causedUUTFailure": false
          },
          {
            "id": 7,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 3sec",
            "start": "2022-11-19T11:45:50.957+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:THowxaJsTE+anr064ixDJC",
            "totTime": 3.0049233,
            "causedUUTFailure": false
          }
        ],
        "seqCall": {
          "path": "C:\\TestStand\\OLC 140 Control Board\\Seq\\OLC 140 Control Board v1.6.seq",
          "name": "JigPowerUp",
          "version": "1.6.0.0"
        }
      },
      {
        "id": 8,
        "group": "M",
        "stepType": "WATS_SeqCall",
        "name": "Power-On test",
        "start": "2022-11-19T11:45:54.117+00:00",
        "status": "P",
        "errorCode": 0,
        "tsGuid": "ID#:0u07T0pyr0S707rp7pTJtB",
        "totTime": 66.4501136,
        "causedUUTFailure": false,
        "steps": [
          {
            "id": 9,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "VA",
            "start": "2022-11-19T11:45:54.307+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:q25e2K/0a0eF04mnKNOSzC",
            "totTime": 0.116143,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 14.9654554895867,
                "highLimit": 16,
                "lowLimit": 14
              }
            ]
          },
          {
            "id": 10,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "5V",
            "start": "2022-11-19T11:45:54.537+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:JFFK1BNV6EaGCtbsJgn7fB",
            "totTime": 0.0455589,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.09013897712155,
                "highLimit": 5.2,
                "lowLimit": 4.85
              }
            ]
          },
          {
            "id": 11,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait for startup - 20sec",
            "start": "2022-11-19T11:45:54.603+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:2ts0P6bg+ECRaHSpds964B",
            "totTime": 20.0043651,
            "causedUUTFailure": false
          },
          {
            "id": 12,
            "group": "M",
            "stepType": "ET_MNLT",
            "name": "ServicePin",
            "start": "2022-11-19T11:46:14.63+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:ndZP3ha/Mkqi7NlI0AwO1A",
            "totTime": 4.8393908,
            "causedUUTFailure": false,
            "reportText": "Unconfigured",
            "numericMeas": [
              {
                "compOp": "LOG",
                "name": "DC_Val",
                "status": "P",
                "unit": "volt",
                "value": 3.84192159040067,
                "highLimit": null,
                "lowLimit": null
              },
              {
                "compOp": "LOG",
                "name": "76Hz",
                "status": "P",
                "unit": "Hz",
                "value": 1.27090948817197,
                "highLimit": null,
                "lowLimit": null
              },
              {
                "compOp": "LOG",
                "name": "76Hz",
                "status": "P",
                "unit": "Hz",
                "value": 1.19174984323338,
                "highLimit": null,
                "lowLimit": null
              },
              {
                "compOp": "LOG",
                "name": "2-3kHz_Freq",
                "status": "P",
                "unit": "Hz",
                "value": 0,
                "highLimit": null,
                "lowLimit": null
              },
              {
                "compOp": "LT",
                "name": null,
                "status": "P",
                "unit": "kHz",
                "value": 2,
                "highLimit": null,
                "lowLimit": 4
              },
              {
                "compOp": "LT",
                "name": "Service Pin State",
                "status": "P",
                "unit": "pin",
                "value": 1,
                "highLimit": null,
                "lowLimit": 3
              }
            ]
          },
          {
            "id": 13,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Reset delay",
            "start": "2022-11-19T11:46:19.513+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:Yfkc/0FC2UCe34/yj+O04C",
            "totTime": 3.0485752,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "millisecon",
                "value": 243.9,
                "highLimit": 325,
                "lowLimit": 150
              }
            ]
          },
          {
            "id": 14,
            "group": "M",
            "stepType": "Action",
            "name": "Apply Power load",
            "start": "2022-11-19T11:46:22.61+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:0XnxAsUNCkuO/PC2c7c/ZB",
            "totTime": 0.6209082,
            "causedUUTFailure": false
          },
          {
            "id": 15,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:46:23.27+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:LwwMFaMdvUSNC7hAHgkqkD",
            "totTime": 1.1087423,
            "causedUUTFailure": false
          },
          {
            "id": 16,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "VA - PowerLoad",
            "start": "2022-11-19T11:46:24.477+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:EQHpw7t0AUy0N0CXNn+X6B",
            "totTime": 3.076374,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 12.6604938913309,
                "highLimit": 13.4,
                "lowLimit": 12.6
              }
            ]
          },
          {
            "id": 17,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "5V - PowerLoad",
            "start": "2022-11-19T11:46:27.573+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:agsEy2ym9Eic+xy20ECENC",
            "totTime": 0.0360331,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.08272863995083,
                "highLimit": 5.2,
                "lowLimit": 4.85
              }
            ]
          },
          {
            "id": 18,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Release Power load",
            "start": "2022-11-19T11:46:27.627+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:9v0P9C12KkWGcxphPmGZjA",
            "totTime": 0.0228638,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "power",
                "value": 0,
                "highLimit": 10,
                "lowLimit": 0
              }
            ]
          },
          {
            "id": 19,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Oscillator test",
            "start": "2022-11-19T11:46:27.667+00:00",
            "status": "E",
            "errorCode": -200284,
            "errorMessage": "DAQmx Read (Counter 1D DBL 1Chan NSamp).vi:1\nProperty: RelativeTo\nCorresponding Value: Current Read Position\nProperty: Offset\nCorresponding Value: 0\n\nTask Name: _unnamedTask<74D>\nSome or all of the sa",
            "tsGuid": "ID#:k2jPuvCTKEygFW4cmbvymC",
            "totTime": 26.5250991,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "S",
                "unit": "Hz",
                "value": 4999867.64410524,
                "highLimit": 5001000,
                "lowLimit": 4999000
              }
            ]
          },
          {
            "id": 20,
            "group": "M",
            "stepType": "ET_A",
            "name": "Reset UUT",
            "start": "2022-11-19T11:46:54.24+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:J33g7SQKgkGArNvSMhrTuD",
            "totTime": 1.0034124,
            "causedUUTFailure": false
          },
          {
            "id": 21,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 5sec",
            "start": "2022-11-19T11:46:55.273+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:Fby6s+20YEuTWHErv7k4QC",
            "totTime": 5.1164606,
            "causedUUTFailure": false
          }
        ],
        "seqCall": {
          "path": "C:\\TestStand\\OLC 140 Control Board\\Seq\\OLC 140 Control Board v1.6.seq",
          "name": "Power-OnTest",
          "version": "1.6.0.0"
        }
      },
      {
        "id": 22,
        "group": "M",
        "stepType": "WATS_SeqCall",
        "name": "Establish contact with UUT",
        "start": "2022-11-19T11:47:00.913+00:00",
        "status": "P",
        "errorCode": 0,
        "tsGuid": "ID#:ro7zFV/toE2EEI40qM0wNC",
        "totTime": 38.216375,
        "causedUUTFailure": false,
        "steps": [
          {
            "id": 23,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Set IP",
            "start": "2022-11-19T11:47:01.52+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:26N9ivz6ckOEe+rIFbGNCA",
            "totTime": 3.5607864,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 24,
            "group": "M",
            "stepType": "ET_MSVT",
            "name": "iLON_Get Templates",
            "start": "2022-11-19T11:47:05.2+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:DP+fqm5eI0+Mrr+XkzKIrA",
            "totTime": 1.8646253,
            "causedUUTFailure": false,
            "stringMeas": [
              {
                "compOp": "Equal",
                "name": "GetTemplates",
                "status": "P",
                "value": "PASSED",
                "limit": "PASSED"
              },
              {
                "compOp": "Equal",
                "name": "HasCorrectProgramID",
                "status": "P",
                "value": "PASSED",
                "limit": "PASSED"
              }
            ]
          },
          {
            "id": 25,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Apply UUT SP - Verify Signal Level",
            "start": "2022-11-19T11:47:07.187+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:qmmQVlYd/E+ebvLaEdFQbA",
            "totTime": 0.7724448,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt rms",
                "value": 1.92324594129317,
                "highLimit": 2.1,
                "lowLimit": 1.8
              }
            ]
          },
          {
            "id": 26,
            "group": "M",
            "stepType": "ET_MSVT",
            "name": "iLON_Read SP",
            "start": "2022-11-19T11:47:07.977+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:K0adAbfHjE+0G7CwE+MPSC",
            "totTime": 1.1854512,
            "causedUUTFailure": false,
            "reportText": "ProgramID: 900082481E041002",
            "stringMeas": [
              {
                "compOp": "Equal",
                "name": "GetServicePin",
                "status": "P",
                "value": "PASSED",
                "limit": "PASSED"
              },
              {
                "compOp": "Equal",
                "name": "NoTimeout",
                "status": "P",
                "value": "PASSED",
                "limit": "PASSED"
              }
            ]
          },
          {
            "id": 27,
            "group": "M",
            "stepType": "Action",
            "name": "MiscUUTInfo_NeuronID",
            "start": "2022-11-19T11:47:09.273+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:vX3pNeYMR0aOCc07bFb4nB",
            "totTime": 1.0569866,
            "causedUUTFailure": false
          },
          {
            "id": 28,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Configure",
            "start": "2022-11-19T11:47:10.4+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:yLLfWqG61UGktvs0HhEnPC",
            "totTime": 24.2243456,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 29,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_CommandsCompleted?",
            "start": "2022-11-19T11:47:34.64+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:hTmH9XqHOEeB4DqIuP6UFC",
            "totTime": 1.0539376,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 30,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 3s",
            "start": "2022-11-19T11:47:35.733+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:nD1MYdnadU2fSpbxvPCY/C",
            "totTime": 3.3349107,
            "causedUUTFailure": false
          }
        ],
        "seqCall": {
          "path": "C:\\TestStand\\OLC 140 Control Board\\Seq\\OLC 140 Control Board v1.6.seq",
          "name": "EstablishContactWithUUT",
          "version": "1.6.0.0"
        }
      },
      {
        "id": 31,
        "group": "M",
        "stepType": "WATS_SeqCall",
        "name": "Test IO",
        "start": "2022-11-19T11:47:39.267+00:00",
        "status": "P",
        "errorCode": 0,
        "tsGuid": "ID#:Rd6L+roD3EaaO1OfbI0K/C",
        "totTime": 14.9593088,
        "causedUUTFailure": false,
        "steps": [
          {
            "id": 32,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Test external memory",
            "start": "2022-11-19T11:47:39.747+00:00",
            "status": "S",
            "errorCode": 0,
            "tsGuid": "ID#:kteBS1VsYECJPL/fz9931D",
            "totTime": 0.0037619,
            "causedUUTFailure": false
          },
          {
            "id": 33,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Test Relay_SET HI",
            "start": "2022-11-19T11:47:39.887+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:LpGASr1CiU2s1yFEz7j+SC",
            "totTime": 0.5279637,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 34,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:40.447+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:h710loyKnUWqEHubTtq5qD",
            "totTime": 1.0536353,
            "causedUUTFailure": false
          },
          {
            "id": 35,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Test Relay - Read back High",
            "start": "2022-11-19T11:47:41.53+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:9mJ3BqUWSkGT+/BnM40AGB",
            "totTime": 0.0444478,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.0891724113881,
                "highLimit": 5.5,
                "lowLimit": 4
              }
            ]
          },
          {
            "id": 36,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Test Relay_SET LO",
            "start": "2022-11-19T11:47:41.597+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:jz1uJDnpC0uDBZn3JZ05nC",
            "totTime": 0.5389224,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 37,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:42.153+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:ZNmjk3M4BUqbfRYZa1irQD",
            "totTime": 1.0041095,
            "causedUUTFailure": false
          },
          {
            "id": 38,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Test Relay - Read back Low",
            "start": "2022-11-19T11:47:43.177+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:sDN1Vc+MHEK+2siauO0J2C",
            "totTime": 0.023841,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.00379226114532533,
                "highLimit": 0.8,
                "lowLimit": -0.4
              }
            ]
          },
          {
            "id": 39,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Test Triac_SET HI",
            "start": "2022-11-19T11:47:43.223+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:LmOiW0vYpUOBQvB/oDIpuD",
            "totTime": 0.668854,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 40,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:43.917+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:xXLLnmR0Z02/Ouiu7xYChD",
            "totTime": 1.0030442,
            "causedUUTFailure": false
          },
          {
            "id": 41,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Test Triac - Read back High",
            "start": "2022-11-19T11:47:44.94+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:Ib91K0ZhLUqM65j4CkKZ3A",
            "totTime": 0.0436178,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.08788365708408,
                "highLimit": 5.5,
                "lowLimit": 4
              }
            ]
          },
          {
            "id": 42,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Test Triac_SET LO",
            "start": "2022-11-19T11:47:45.007+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:B96gEFUQS06NqjrwfwSKmC",
            "totTime": 0.4557367,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 43,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:45.483+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:a+y5ODSZYUi06vK2Y4YqiD",
            "totTime": 1.0042137,
            "causedUUTFailure": false
          },
          {
            "id": 44,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Test Triac - Read back Low",
            "start": "2022-11-19T11:47:46.51+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:Uvi2wgkYmkWWmPUB+TuTUD",
            "totTime": 0.0292104,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0,
                "highLimit": 0.8,
                "lowLimit": -0.4
              }
            ]
          },
          {
            "id": 45,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Test IO1_SET HI",
            "start": "2022-11-19T11:47:46.567+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:wQxw9AKz70OH4bJ+nkV6kC",
            "totTime": 0.6545134,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 46,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:47.24+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:DhgyJICdHkCeunxZJsA+KB",
            "totTime": 1.015926,
            "causedUUTFailure": false
          },
          {
            "id": 47,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Test IO1 - Read back High",
            "start": "2022-11-19T11:47:48.27+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:pkxglFwTqkaSnfz5xnYqiA",
            "totTime": 0.0636327,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.08659490278834,
                "highLimit": 5.5,
                "lowLimit": 4
              }
            ]
          },
          {
            "id": 48,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Test IO1_SET LO",
            "start": "2022-11-19T11:47:48.357+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:Mvj7V7zGokqP9nTRn0BzOB",
            "totTime": 0.4824627,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 49,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:48.857+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:RwnqxjFBaEGOdgS0M3/iKB",
            "totTime": 1.0040072,
            "causedUUTFailure": false
          },
          {
            "id": 50,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Test IO1 - Read back Low",
            "start": "2022-11-19T11:47:49.88+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:zNPv5lQDPUG5AdxAgfOjdD",
            "totTime": 0.0259645,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.000892603030963491,
                "highLimit": 0.8,
                "lowLimit": -0.4
              }
            ]
          },
          {
            "id": 51,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Test IO2_SET HI",
            "start": "2022-11-19T11:47:49.93+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:tdad6bx0s0uwEkaWHk0e6A",
            "totTime": 0.5734813,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 52,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:50.517+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:PZdRTN7bK0mcbe7n6sUDaC",
            "totTime": 1.0127161,
            "causedUUTFailure": false
          },
          {
            "id": 53,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Test IO2 - Read back High",
            "start": "2022-11-19T11:47:51.547+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:nMEuNcP/90WmmoKD/P911C",
            "totTime": 0.0460416,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.08788365708408,
                "highLimit": 5.5,
                "lowLimit": 4
              }
            ]
          },
          {
            "id": 54,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "iLON_Test IO2_SET LO",
            "start": "2022-11-19T11:47:51.617+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:ZHVlHw0qgUmIqlPJlTsnuA",
            "totTime": 0.4110341,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 55,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:52.047+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:kZjix7TytUyVzoqYudgqsA",
            "totTime": 1.0301035,
            "causedUUTFailure": false
          },
          {
            "id": 56,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Test IO2 - Read back Low",
            "start": "2022-11-19T11:47:53.127+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:XKzIUI357UqLRL9S7KQN5C",
            "totTime": 0.0433033,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.000892603030963491,
                "highLimit": 0.8,
                "lowLimit": -0.4
              }
            ]
          },
          {
            "id": 57,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:53.197+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:cby0+ky13E63gEBWWdXH9B",
            "totTime": 1.0042332,
            "causedUUTFailure": false
          }
        ],
        "seqCall": {
          "path": "C:\\TestStand\\OLC 140 Control Board\\Seq\\OLC 140 Control Board v1.6.seq",
          "name": "TestIO",
          "version": "1.6.0.0"
        }
      },
      {
        "id": 58,
        "group": "M",
        "stepType": "WATS_SeqCall",
        "name": "DALI Test",
        "start": "2022-11-19T11:47:54.317+00:00",
        "status": "P",
        "errorCode": 0,
        "tsGuid": "ID#:rp4VxXceHEyCbPnwhRwHID",
        "totTime": 21.2800767,
        "causedUUTFailure": false,
        "steps": [
          {
            "id": 59,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Set TestMode",
            "start": "2022-11-19T11:47:54.927+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:Y1MUQDraWk+23XSpVVsOOC",
            "totTime": 0.8557554,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 60,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read UUT_5V",
            "start": "2022-11-19T11:47:55.8+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:4YJHvs0ad0qvfyyFEnUF9B",
            "totTime": 0.0264198,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.0869170913615,
                "highLimit": 5.25,
                "lowLimit": 4.75
              }
            ]
          },
          {
            "id": 61,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Comp1 ref",
            "start": "2022-11-19T11:47:55.857+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:CJ9/Cgob90ig5ZQwUJiuCD",
            "totTime": 0.0435865,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.156829776993753,
                "highLimit": 0.167868264014929,
                "lowLimit": 0.152607512740845
              }
            ]
          },
          {
            "id": 62,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Comp2 ref",
            "start": "2022-11-19T11:47:55.923+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:Y6Bft+aFVE29fKk6iwanJA",
            "totTime": 0.0571059,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.208379258233272,
                "highLimit": 0.213650517837183,
                "lowLimit": 0.20347668365446
              }
            ]
          },
          {
            "id": 63,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Set Clamp",
            "start": "2022-11-19T11:47:55.997+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:j0SxVPjfPU+bjN6hspUyxC",
            "totTime": 0.7815742,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 64,
            "group": "M",
            "stepType": null,
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:56.797+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:pCc5A/FXiEejAMw7BDhJtB",
            "totTime": 1.0039717,
            "causedUUTFailure": false
          },
          {
            "id": 65,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Cur drive",
            "start": "2022-11-19T11:47:57.82+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:5AS1/bTha0WYVh2bkAdeAA",
            "totTime": 0.0595098,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": -1.00039613390792012,
                "highLimit": 0.1,
                "lowLimit": -0.1
              }
            ]
          },
          {
            "id": 66,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Clm drive",
            "start": "2022-11-19T11:47:57.903+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:Fte+UNv++0OC6vqEK1GBuA",
            "totTime": 0.0493336,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.04728790073797,
                "highLimit": 5.25,
                "lowLimit": 4.75
              }
            ]
          },
          {
            "id": 67,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI+ Output",
            "start": "2022-11-19T11:47:57.977+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:4HzHQi+dvkyrqjnGKqwJoA",
            "totTime": 0.049656,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.00565141688049773,
                "highLimit": 0.1,
                "lowLimit": -0.1
              }
            ]
          },
          {
            "id": 68,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI- Output",
            "start": "2022-11-19T11:47:58.05+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:a1G7ak79nUCKDXQfNKpiTB",
            "totTime": 0.0479125,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.00765847196854245,
                "highLimit": 0.1,
                "lowLimit": -0.1
              }
            ]
          },
          {
            "id": 69,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Set Current",
            "start": "2022-11-19T11:47:58.123+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:dTgjiOyCbEWgMrNkd7YR7C",
            "totTime": 0.7491933,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 70,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:47:58.893+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:XdtDH+50/UqV5qeXfzmX9D",
            "totTime": 1.0034384,
            "causedUUTFailure": false
          },
          {
            "id": 71,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Cur drive",
            "start": "2022-11-19T11:47:59.917+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:JU93IaljIk6Lwv+NeQSLUC",
            "totTime": 0.0300639,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.04632133521037,
                "highLimit": 5.25,
                "lowLimit": 4.75
              }
            ]
          },
          {
            "id": 72,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Clm drive",
            "start": "2022-11-19T11:47:59.97+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:YmIEgfrnlk6b1TweXNzaZD",
            "totTime": 0.0237301,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0,
                "highLimit": 0.1,
                "lowLimit": -0.1
              }
            ]
          },
          {
            "id": 73,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI+ Output",
            "start": "2022-11-19T11:48:00.017+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:unZTfQAvhU+VR2XBToRAEA",
            "totTime": 0.0319437,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 15.0105625515711,
                "highLimit": 16,
                "lowLimit": 14
              }
            ]
          },
          {
            "id": 74,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI- Output",
            "start": "2022-11-19T11:48:00.077+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:ZP1deUipDUKATMoebEUu1C",
            "totTime": 0.0249875,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.000892603030963491,
                "highLimit": 0.1,
                "lowLimit": -0.1
              }
            ]
          },
          {
            "id": 75,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Set Clamp_Current",
            "start": "2022-11-19T11:48:00.12+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:5tdI7LLprEulofb73DTc0D",
            "totTime": 0.8460925,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 76,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:48:01.063+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:xmLp66m/h0Ox0E2NPmzQcD",
            "totTime": 1.0340789,
            "causedUUTFailure": false
          },
          {
            "id": 77,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Cur drive",
            "start": "2022-11-19T11:48:02.117+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:KiXAkrhI0kC7i12gv0wzZB",
            "totTime": 0.0269559,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.04922103180705,
                "highLimit": 5.25,
                "lowLimit": 4.75
              }
            ]
          },
          {
            "id": 78,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Clm drive",
            "start": "2022-11-19T11:48:02.167+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:+akLEQNt90iD3vKBOjxQWC",
            "totTime": 0.0299862,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 7.04857665478197,
                "highLimit": 5.25,
                "lowLimit": 4.75
              }
            ]
          },
          {
            "id": 79,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI+ Output",
            "start": "2022-11-19T11:48:02.22+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:d0Xpf1wVTUOlADR/XUTdDD",
            "totTime": 0.0258502,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 1.27505750592495,
                "highLimit": 1.5,
                "lowLimit": 1.1
              }
            ]
          },
          {
            "id": 80,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "DALI+ Out",
            "start": "2022-11-19T11:48:02.273+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:zX4QlsP4nkWj4Qctfm/pnD",
            "totTime": 0.045653,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 1.2828642494487,
                "highLimit": 1.5,
                "lowLimit": 1.1
              }
            ]
          },
          {
            "id": 81,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI- Output",
            "start": "2022-11-19T11:48:02.343+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:LfIYnP/cvEyK+ueuxW+XjA",
            "totTime": 0.0265699,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.258640003717397,
                "highLimit": 0.3,
                "lowLimit": 0.2
              }
            ]
          },
          {
            "id": 82,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Set Current",
            "start": "2022-11-19T11:48:02.39+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:0btmfkREdkWHdqHW1wJGzB",
            "totTime": 0.8989078,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 83,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:48:03.303+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:hlECHPpAXUu4szoHdskJyD",
            "totTime": 1.0110436,
            "causedUUTFailure": false
          },
          {
            "id": 84,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Cur drive",
            "start": "2022-11-19T11:48:04.333+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:Usjhg/ja30OBJMKNyw2kSA",
            "totTime": 0.0258793,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 5.04986540883419,
                "highLimit": 5.25,
                "lowLimit": 4.75
              }
            ]
          },
          {
            "id": 85,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read Clm drive",
            "start": "2022-11-19T11:48:04.387+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:U+iZQ1JJGUmVDygPbixWND",
            "totTime": 0.0236977,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": -0.000718318142561308,
                "highLimit": 0.1,
                "lowLimit": -0.1
              }
            ]
          },
          {
            "id": 86,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI+ Output",
            "start": "2022-11-19T11:48:04.427+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:eYmip+4dS0OrEHl5/B2PMD",
            "totTime": 0.0368052,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 14.9983192054507,
                "highLimit": 16,
                "lowLimit": 14
              }
            ]
          },
          {
            "id": 87,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI- Output",
            "start": "2022-11-19T11:48:04.483+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:krcks14esUu93s1c/gensA",
            "totTime": 0.0249867,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.000892603030963491,
                "highLimit": 0.1,
                "lowLimit": -0.1
              }
            ]
          },
          {
            "id": 88,
            "group": "M",
            "stepType": "Action",
            "name": "Apply DALI_Short",
            "start": "2022-11-19T11:48:04.533+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:X9bDIfoZgEikUWamuAn6OB",
            "totTime": 0.0205132,
            "causedUUTFailure": false
          },
          {
            "id": 89,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:48:04.573+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:y1+yP0YTMUmNVpi1Ic3M+D",
            "totTime": 1.0038234,
            "causedUUTFailure": false
          },
          {
            "id": 90,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI+ Output",
            "start": "2022-11-19T11:48:05.597+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:nkhD0Y/6iUuWSDB1diBZID",
            "totTime": 0.0250937,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.262110073663651,
                "highLimit": 0.3,
                "lowLimit": 0.22
              }
            ]
          },
          {
            "id": 91,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI- Output",
            "start": "2022-11-19T11:48:05.647+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:P2sWahoaXkO/map0FW05iD",
            "totTime": 0.0910646,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.257029082367037,
                "highLimit": 0.3,
                "lowLimit": 0.22
              }
            ]
          },
          {
            "id": 92,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Read CMP1",
            "start": "2022-11-19T11:48:05.777+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:02po3aVdkEyZw1gdhK9Y9B",
            "totTime": 0.9536997,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 93,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:48:06.763+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:T0z4E5jSs0SUznRwiWY+FA",
            "totTime": 1.0142973,
            "causedUUTFailure": false
          },
          {
            "id": 94,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Read CMP2",
            "start": "2022-11-19T11:48:07.807+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:LhMybNlPik+3SCAwwbbHQA",
            "totTime": 0.7855345,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 95,
            "group": "M",
            "stepType": "Action",
            "name": "Release DALI_Short",
            "start": "2022-11-19T11:48:08.617+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:PqH6ZWKMmUGZ6bA9pg0jwD",
            "totTime": 0.0165163,
            "causedUUTFailure": false
          },
          {
            "id": 96,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:48:08.663+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:Wgha1pkkckChpQYQIV0rzD",
            "totTime": 1.0036776,
            "causedUUTFailure": false
          },
          {
            "id": 97,
            "group": "M",
            "stepType": "Action",
            "name": "Apply DALI_Load",
            "start": "2022-11-19T11:48:09.693+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:S5JyLIsNEEeYW00ATfT+UB",
            "totTime": 0.0160143,
            "causedUUTFailure": false
          },
          {
            "id": 98,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:48:09.737+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:L9+c9om+mEyfaCMbv4zeTB",
            "totTime": 1.0061938,
            "causedUUTFailure": false
          },
          {
            "id": 99,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Read CMP1",
            "start": "2022-11-19T11:48:10.777+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:TmGUkqoB/EufWimI+LWC5B",
            "totTime": 0.8188904,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 100,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:48:11.62+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:QDoAElx/70GMg4KFLbfLnA",
            "totTime": 1.0036857,
            "causedUUTFailure": false
          },
          {
            "id": 101,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Read CMP2",
            "start": "2022-11-19T11:48:12.707+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:SdnHgFuYQE6cnv9uEYekVC",
            "totTime": 0.8736828,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          },
          {
            "id": 102,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI+ Output",
            "start": "2022-11-19T11:48:13.603+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:OPIrjOUDGEifjFf0fnfbVC",
            "totTime": 0.0293289,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.180275274804324,
                "highLimit": 0.21,
                "lowLimit": 0.16
              }
            ]
          },
          {
            "id": 103,
            "group": "M",
            "stepType": "ET_NLT",
            "name": "Read DALI- Output",
            "start": "2022-11-19T11:48:13.663+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:PnVttO0AoECWhVFouHlWaC",
            "totTime": 0.0245012,
            "causedUUTFailure": false,
            "numericMeas": [
              {
                "compOp": "GELE",
                "name": null,
                "status": "P",
                "unit": "volt",
                "value": 0.172938989746286,
                "highLimit": 0.21,
                "lowLimit": 0.16
              }
            ]
          },
          {
            "id": 104,
            "group": "M",
            "stepType": "Action",
            "name": "Release DALI_Load",
            "start": "2022-11-19T11:48:13.72+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:gEs2bhzxJUGUbzB744vPyD",
            "totTime": 0.0191033,
            "causedUUTFailure": false
          },
          {
            "id": 105,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait 1sec",
            "start": "2022-11-19T11:48:13.773+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:BLIakjciiU2cZzIY7/X3DD",
            "totTime": 1.0061332,
            "causedUUTFailure": false
          },
          {
            "id": 106,
            "group": "M",
            "stepType": "ET_PFT",
            "name": "DALI_Clear TestMode",
            "start": "2022-11-19T11:48:14.807+00:00",
            "status": "P",
            "errorCode": 0,
            "tsGuid": "ID#:5xvW0+ijxkKksWywPMFGyB",
            "totTime": 0.7648818,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": null,
                "status": "P"
              }
            ]
          }
        ],
        "seqCall": {
          "path": "C:\\TestStand\\OLC 140 Control Board\\Seq\\OLC 140 Control Board v1.6.seq",
          "name": "DALITest",
          "version": "1.6.0.0"
        }
      },
      {
        "id": 107,
        "group": "C",
        "stepType": "ET_PFT",
        "name": "iLON_Unconfigure",
        "start": "2022-11-19T11:48:15.857+00:00",
        "status": "P",
        "errorCode": 0,
        "tsGuid": "ID#:DiPX3C2iW0eqb0XBAogsmA",
        "totTime": 6.5503012,
        "causedUUTFailure": false,
        "booleanMeas": [
          {
            "name": null,
            "status": "P"
          }
        ]
      },
      {
        "id": 108,
        "group": "C",
        "stepType": "NI_Wait",
        "name": "Wait 20s",
        "start": "2022-11-19T11:48:22.42+00:00",
        "status": "D",
        "errorCode": 0,
        "tsGuid": "ID#:A7dJ/n4r606ytaqLR2GJuA",
        "totTime": 20.0099753,
        "causedUUTFailure": false
      },
      {
        "id": 109,
        "group": "C",
        "stepType": "Action",
        "name": "Clear Test",
        "start": "2022-11-19T11:48:42.443+00:00",
        "status": "D",
        "errorCode": 0,
        "tsGuid": "ID#:J407ETJ00kOsSpSK3hfJfA",
        "totTime": 0.3799745,
        "causedUUTFailure": false
      }
    ],
    "seqCall": {
      "path": "C:\\TestStand\\OLC 140 Control Board\\Seq\\OLC 140 Control Board v1.6.seq",
      "name": "C:\\TestStand\\OLC 140 Control Board\\Seq\\OLC 140 Control Board v1.6.seq",
      "version": "1.6.0.0"
    }
  },
  "uut": {
    "execTime": 174.205173,
    "testSocketIndex": -1,
    "batchSN": null,
    "comment": null,
    "errorCode": 0,
    "errorMessage": null,
    "fixtureId": null,
    "user": "Janis",
    "batchFailCount": 0,
    "batchLoopIndex": 0,
    "stepIdCausedUUTFailure": null
  },
  "miscInfos": [],
  "subUnits": [
    {
      "partType": "NeuronID",
      "pn": "OLC-140-C",
      "rev": "8",
      "sn": "050200929F00",
      "position": 0
    }
  ],
  "assets": [],
  "assetStats": [],
  "additionalData": []
}"""

import collections


def deep_update(mapping, *updating_mappings):
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping


def update(orig_dict, new_dict):
    for key, val in new_dict.iteritems():
        if isinstance(val, collections.Mapping):
            tmp = update(orig_dict.get(key, {}), val)
            orig_dict[key] = tmp
        elif isinstance(val, list):
            orig_dict[key] = (orig_dict.get(key, []) + val)
        else:
            orig_dict[key] = new_dict[key]
    return orig_dict


def validate_json_data(jfile):
    e_loc = []
    message_dict = {}
    try:
        m = UUTReport.parse_obj(jfile)
        print(m.root)
        print(m.json(indent=2))
    except ValidationError as exc_info:
        error_list = json.loads(exc_info.json())
        from types import SimpleNamespace
        for i, error in enumerate([SimpleNamespace(**error) for error in exc_info.errors()], start=1):
            print(f"{i:<2} {error.type:<28} | {str(error.loc):<55} | {error.msg}")
        for error in error_list:
            error['loc'] = tuple([loc for loc in error['loc'] if loc != '__root__'])
        print(error_list)
        for loc in error_list:
            if '__root__' in loc["loc"]:
                loc1 = list(loc["loc"][0:-1])
                loc1.append('status')
                e_loc.append(tuple(loc1))
            else:
                e_loc.append(loc["loc"])

        # e_loc = [e_loc]
        print(e_loc)
        message_dict = {}
        for loc in error_list:
            keys = loc['loc']

            if '__root__' in keys:
                keys = list(keys[0:-1])
                keys.append('status')
                keys = tuple(keys)

            result = jfile
            last_step = ("", "")
            print(keys)
            for key in keys:
                if type(result) is dict:
                    if 'stepType' in result:
                        last_step = (result['id'], result['name'])
                result = result[key]

            if isinstance(result, list):
                result = f"\"{keys[-1]}\" list object"
            if isinstance(result, dict):
                result = f"\"{keys[-1]}\" dict object"

            if last_step == ("", ""):
                print(len(keys))
                message_dict[keys] = (f"{'-' * 100}\n"
                                      f"\n"
                                      f"Field Name: {keys[-1]} \n    -> \"{keys[-1]}\": {result}\n    -> {loc['msg']}\n"
                                      f"\n"
                                      f"{'-' * 100}\n")
            else:

                message_dict[keys] = (f"{'-' * 100}\n"
                                      f"\n"
                                      f"Step ID: {last_step[0]}, Name: \"{last_step[1]}\"\n    -> \"{keys[-1]}\": {result}\n    -> {loc['msg']}\n"
                                      f"\n"
                                      f"{'-' * 100}\n")

    return e_loc, message_dict


import PySimpleGUI as sg


def create_layout():
    return [[sg.Input(key='-ID-'), sg.FileBrowse()],
            [sg.Text("WATS Report"), sg.Text(f"{' ' * 120}"), sg.Text("Error List")],
            [sg.Multiline(size=(80, 30), key="-DASHBOARD_TEXTBOX-"),
             sg.Multiline(size=(60, 30), key="-DASHBOARD_TEXTBOX2-")]]


layout = [[create_layout()],
          [sg.Button("Validate"), sg.Button("Refresh"), sg.Cancel()]
          ]

window = sg.Window('Dr WATS', layout)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break

    if event == 'Validate':

        # WATSTOKEN = 'dGVzdDoqazFRQTk5MnlZMUpZV0hwOWNLa2tZTDl4ODZ2OG8='
        # request_url = 'https://akgre.wats.com/api/Report/WSJF'
        # headers = {'Accept': 'application/json', 'Authorization': 'Basic ' + WATSTOKEN}
        # # response = requests.post(request_url, headers=headers, data=json.dumps(json.loads(json_data)), timeout=30)
        #
        # response = requests.get(f'https://akgre.wats.com/api/Report/Wsjf/{values["-ID-"]}', headers=headers, timeout=60)
        #
        # print(response.status_code)
        # print(response.json())

        e_loc, message_dict = validate_json_data(json.loads(json_file))


        def extract_keys(data):
            keys = []
            for key, value in data.items():
                keys.append((key,))
                if isinstance(value, dict):
                    keys += [(key,) + subkey for subkey in extract_keys(value)]
                elif isinstance(value, list):
                    for i, element in enumerate(value):
                        keys += [(key, i) + subkey for subkey in extract_keys(element)]

            return keys


        json_loc = extract_keys(json.loads(json_file))
        line_list_json = list(json.dumps(json.loads(json_file), indent=4).split("\n"))
        complete_list = []
        for i, x in enumerate(line_list_json):
            if ":" in x:
                print((i, json_loc[0], x))
                complete_list.append((i, json_loc.pop(0), x))
            else:
                complete_list.append((i, "", x))
        for y in complete_list:

            if y[1] in e_loc:
                print(y[1], e_loc)
                window["-DASHBOARD_TEXTBOX-"].print(y[2], background_color='yellow')
                window["-DASHBOARD_TEXTBOX2-"].print(message_dict[y[1]])

            else:
                window["-DASHBOARD_TEXTBOX-"].print(y[2])

window.close()

json_data = r"""
{
  "type": "T",
  "id": "f66c8c85-7375-4d94-9d0d-bdb981667820",
  "pn": "OLC-140-CA",
  "sn": "12388rrefej",
  "rev": "8",
  "processCode": 1100,
  "result": "P",
  "machineName": "wats-demo-01",
  "location": "skyWATS",
  "purpose": "demo",
  "origin": null,
  "start": "2022-12-28T13:07:05.92+02:00",
  "startUTC": "2022-12-28T11:07:05.92Z",
  "root": {
    "id": 0,
    "group": "M",
    "stepType": "WATS_SeqCall",
    "name": "MainSequence Callback",
    "status": "P",
    "steps":[
      {
        "id": 11,
        "group": "S",
        "stepType": "NI_Wait",
        "name": "Jig Power-up1",
        "status": "P",
        "steps": [{
            "id": 1,
            "group": "M",
            "stepType": "Statement",
            "name": "Jig Power-up2",
            "status": "F"},
            {
            "id": 12,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Jig Power-up3",
            "status": "P"}
            ],
        "seqCall": {
      "path": "seq path",
      "name": "seq name",
      "version": "version_number"
    }
        },
        {
        "id": 2,
        "group": "M",
        "stepType": "CallExecutable",
        "name": "Jig Power-up1",
        "status": "F",
        "tsGuid": "123456789012345678901234567890",
        "totTime": 9999999999999999999999999999999999999999999,
        "reportText": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\naaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "messagePopup": {
             "response": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
             "button": -32768
            },
        "attachment": {
            "name": "WiFiNotification",
            "contentType": "image/png",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAMgAAADICAYAAACtWK6eAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAALEwAACxMBAJqcGAAAEjVJREFUeJztnXuUVdV9xz93ZngN72EAkeExOCAqqFhjRFCMgrGGJMtEE1ZMajUaUdOnkualaYxVWhvNippU8zDBRI2YNG01hWq1iUbrI6JEVIg4YOUNQ0hAAojpH997150ZZuDeuWefc+69389aZ81aMHP27+y9f/vx27/9+4ExxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhiTAJmkBahwhgAjgQZgWLunAegP9O7iAdjbxbML2Aa0ZX/mns3Ab2P5mirEClIatcBE4BhgAjAOGJ/9OQ54B3Xg9h0618F30bUiQNeK05+8crVXtpGoHdcCa7I/1wKrgZeB3wD7A3x7VWAFKZwhwLuB44CpwBRgErAeeAl1yM6ddEdMsg2mo2KOA1qyMo4CVmVl/DXwIvA0nnUKwgrSNRngKGA6cEr2ZxPwLPAC6mgvoRH6rYRkLJR64GjySn08cCLwJvBUu+cV4I8JyZharCB5DgfOAt4LzEYjbK7zPIkUolKWKrVIYdoPAIOAR4D/ApYCGxKTzqSCGmAWcBOwHNgK3AdcBIxOUK6kaAIuBn6E6mI5qptZqK5MFVALnAF8E42QzwFfBN6FO0F7aoCTgGuAX6G6+gaqu9oE5TKBmAncAWwCngEWAM2JSlReTAA+g+puE/AvwIxEJTIlMxI16qvACuBqZN0xpTEODTAvo439AlTXpgzIAOcAP0XnDd8CTk5UospmOqrjNlTn78OGn1TSH7gCWImWARdl/83EQ39U58+gNrgCmZdNwjQBC4EtwI/xujgNzEBtsRm4keq0CCZOM/Bd5LLxNbzhTiPNqG22Ad/BbRQL44FvIzv9l5H7h0k3Q1BbbUX7FRtKAjAGuBNV8nXA0GTFMT1gKPAV1IZ3oDZNPWm3OAwAPg98Ctneb0YWk3KgP3nv3sM50N19KNCPwtzddwPbOdDVfT1558hdwb8oGhqAq4DLUJsuBHYmKtFBSKuC1CCryHXAw0hJ1icqUdfUoEO0Ke2eFqQY9cAbqPO+yYEu723AHyjM3b0veTf39u7uTdmyxiKnybXIvX0Fee/d10mnE+Jo4Abk93YN8D10PSBVpFFBZqHN3e+Bv0GuDmlhHLL9T0eu71PQkiHn3fsSci1fi6w4cTIiK98k8so6FSnSCuTinnO+XBuzbAfjROAWNOP+NfCLZMVJL8PQKLIGOC9RSfI0A/OBxcA65JP0E3R6PBMYmJxoBTMQyboAyb4Bfcti9G1psS6dj9r+LjRLmnZ8HDXczSR7wNcXmAvchpYqG4DvI/nS0pGioBl90yL0javQN89FdZAU/dFssgG4IEE5UkMzsARYhqbaJKhHM9Z9aCP8KBptjyOdS9CoyaBvXQD8N6qD+4APIyNCErwLXUxbQmUNTEVxGToBXwDUxVx2LRot70cXo5YClwKNMcuRRhpRXSxFdXM/qqu43dzrkLPpFmTFrBqGA/+ONt+TYy67BVlO1gFPAJfg9e7BaAA+iepqHaq7lphlmIz6yr+hvlPRnIMq+kagV0xl1qLlwv8AG4F/In7FrAQmo7rbgOryPOKbVXqhPrMO+NOYyoyVPmgT2AqcGlOZg5CZuBV4HClJXEpZydQBH0J12orqeFBMZZ+GLF23kj9ULXvGIjfoxSg8TWhGAV9F5xM/JLnNfzVwIqrjrcgCOSqGMgcDD6BznbJwVzkYs9GUfFUMZR2GTIRbkYI0xVCmEU3kB6VbUFuE5mrkXXFmDGVFTga5h6xDJ+MhGUG+cW7G1z+TZCRqg9wgNSJweacjJfls4HIipR5dmPklctILRV+khFuQa0oco5YpjNxsvgW1UcjDx9HIfeYBkju3KZiRaL9xF2E3xPPQZm0xVXyQVAY0ozZqBT4asJzeyE3paVK8gjgaVcQ1AcuYhmamZ4nPGmZK51QUg+yXqA1DcS3yXj4qYBk94kwULymU/0w9ivK3EfhzqsMFpNLIoLbbiNoyVFCHj6O+eEag9xfNBeijTwv0/rPQqLAIu4JUAo3A3ahNzwpUxizUJz8W6P0Fcxnwf4SZ0gYjpVhNuIo0yTEHte0iwpyPHY365qUB3l0Qf4tGgQkB3p07Mb0Nx1eqZOrRqXgrYVYgR5A/7Y+VL6EAYVEfxvVCd5Qr1ufGdMnZ6FpyCB+9MaivhjQedWAhCo0ftTntCOS1+VO816hGGlHbP4f6QpSMRH12YcTvPYDLswVF7SL+fmR5uDzi95ry43K0wZ4b8XsbUOyAK4r5o2LMpYdlC5gOvFZMIQehBkUu+QS6k/xMRO9NMzUomNowug79A12H/NmGLjClLvJHAE5CB4yL0HI+qm+eiE7dj0ED8iEpRkGuRVPVlcXL1SUNwL3IfXoeckuoBDLkQwG10DG55mhksfk9+fA/nUP/QPchfwaixKDr6Jgw9DUUUSWtIX56wnDUP95G5tqo4qHdjpTjukJ+uRgFeRp5UD7eA6E60wI8hG6JfY7yzf2XQebEXBig45DJOxcK6Dd0zHr7JpoNejoi1iBlGU1HxcuF+mlEOTtymWyfQnk8ylVpatEtxg+i1AqrI3jnqeigMvK0GL8lGnv1DOQCf0kE70qCY9E9+iWos69EfkDzUaUnGQpoYFaG+Sgayyok4xIk87HJiVYSlyCv3ekRvGsIgVJg70Y3A0vhoyigWjkd/PUFzkVKsB51uluBD1Ae1rZGNALnQhmtR99yLsmG+CmWOWjz/pES39MHLWsjZzWlXdi/Ci0zpkYjTlD6oiu6uVBAjyDrSiV4Dk9AlpxH6BjipxyUZQpaspZy8NdCNEu1A1hEz82wf49yBab9lt8JaBO3FeULr/RQQLkQPw+jb74d1UGaORztq77Uw7+fj/py5LwHbQCLjWH1z2jTGPp2WU/pizrJMmQFuoYKuOvcA8agb38d1cWlpHdWGY5kvKnIv6tDyhXM0/dB4PoCfzeD8pE/TTrzeRyG8lVsQnG6ZmM3elAdzAb+A9XNV0jnbc0hyEr3DQpvt+uR9TQYjchqcy0HF6oe2bB/TvoCPI9BeSna0JJiUrLipJpJqAO2oTpL28w6AHgMuIeDO7XWoGX+KmIIPjcyK9QzKHhYewUYgdZ4rchSkqYpugk19lZkWx+WrDhlxTDkSLgN1WGa9pJ9UV97HV2/aL+UH4g8NJ5FfTa267gZZPlYgrIDbSJ/MvwjFG4/LQwC/hEpxkIqe9MdmkZUl9tQlMW4AsYVwkzU93JZuDahvrkE9dXEls81SGvTNiLXohFlA0r8mcZ1dLkyCmUZ3oDqOO7A1odiGOqTNUkLklbejSxnjwLHJyxLJTMNxel9EdW5STkDgK+j0+KQYWZMR+ahOv86aoOKoZLMmmej9MIPI7+j7cmK0yV1aIM7nHwizsFoo9mb/G26fciz9w/IezeX/HMz8uR9O1apC2MoOvOajQw1/5msONFQCQrSDzXM+1Bm3MeSFQeQteRY8ok0JyLv25Fo87iR/GZyO7CHvLt7hryrex/U8Rqyzyi0tt6I3HZWkU8eupwC7zgE5j0ocOCDaKDanaw4pVHuCnICii7+K3RPZUcCMuRSmM1C3qYno0OsF1B22RXo9HYNcncvdfTPzULjkav9MdlnGlK2XCbbnyOlScLVfTAyB09DYaGWJSBD1XMlGjHnJVD2YNTwd6PRvBVZyi5GnTaJgacGKcrFWVnWICvTInThKI7UE535GFoWFnXN1ZRGP9ToLxD95f6DMQhFBnyIvH39CuJPSVYME9FAshTdYnwQuJB4zy9a0Ez2fcoguHS5MwEpxiLiq+xZ2fJ+h5TjE2gJVW4MBf4MfcMO1GFDRcPsTD3wA9R2lXBlIJVMR0uGT8dQVj1y7X8VeTAvoLIOGkehDLK575tPPAH6/gK1YeTXXaud89Fa9uzA5QxHflpb0XJkTuDykiaDbnc+hIJm/APhPSLOQW15XuByqoargTeQpSgUOR+j7cB30Nq92piE3EfakGNiSEU5HsXNjSM1X0VzAzKTjg70/n7oklAbOmQcH6iccqIZuBOd0XyBcB7ZTcj8Xej9ItOODEqr9jxhvG8zyEz7BvATqnPGOBSTUCjQtYRLIzActfEtgd5fkWTQCPYkYWz3RyIHu+dxlqpCOA0d9D1GmIEkdzPwTsr/4DoWrgOeIHqnt15oObUFRcVIm4t2mqlF+4WtwBeJPgL7ANTmBUU7rGamotPxqAM8TEbuKD8jfddGy4mx6ID0OTQTR8kIZAKeEvF7K4q7gL+L+J1XolnDkeOjI1SdXo36gOmGrUQ3wg9EubOfw5vwEByJZuX7iW45fDjqA6YLhhNd5RyFTonvoPRwqaZ7+gDfQubayRG9M8QSuyIYiw6PSmUuOqm9MIJ3mcK4CHXscyJ4Vys+j+qSfsBbFB+5sT2fRjfuTopEIlMMJ6Nrt6XsS2qBXThxa7c8D5zeg7/LAF9Fp+7jI5THFEczWm7dRM/ONGaiPmC64a/QyXYx1CD/qcdJ5lKQ6cgQdKbxbYoPu/MA6gOmG/qiHBaFenrWoRCnS/G0nCb6o+AZ91D4kvnDqO3TFI0zlUf7x6PDqPnIF6g7BqIG2I9C/OwJL1pJ9EKm0WPQxa+xyKw5DI26/egY1WQ3yoS0Da3t30B5LV5G8ZH3xSh7T+iDTMAZ5Mu18yC/ey6K/ftedKnKHIITUKzVHwIndvq/QcAn0Z3r2yhtUx+SBnSP5VYUG3YvCqAQxbM3+85bs2VEnZY7KupQgPBWdFe+/VXfDGrbe5DiT4tdujKnHt16ewXd0/g1yub6O7RPOSU50bplIvBZlPJhP9EpxKGe/cD/Ii+ENN6RnwH8K2q711Bbbkez4Wfw8rhkGpCPzhGkb8YYCHwKeaTGpRCHep7KypS21BO9kAJPIb2znomIZnRnZQfJK0R3z46sjA6UYGKjBeWj2EfyClDosy8rcxqXX6ZCaESb4nJSjM7PXhRgOm2pKkwZk0Em5+0k38GjetrQHiWNZn5TRkxEp8JJd+hQzxN42WV6yGXocCvpThz62Zn9VmMKYgBwH8l33Life5GLiDHdcgQ6vEq6syb1rEBuMMYcwAx0zzrpTpr0s5l0eimYBJmLnAOT7pxpeXajjF3GcD7ROhJWyrMXB5iueuaglGhJd8bcqL0l+6RlNtuHknJWLdV8UNQfXdAZFWOZb5HPIbgyW/5qdAi5v9Pv1qKkNy3oPOZI8jkQ4/R+XZcte1eMZZoU8JfEMwq3onQCJxNNyM5eSFEWojsxcXxDHEmLTMr4BeE61F6U4uwUws7SGWR9W0TYfdRjAb/BpJQQvlU7UXSVphi/I8cYlEZgVxHyFvq0xfgdJiVEfePvHsIl+imGJqL3BOi8PzJVQFSHgiuJL1tsMZwOrCKab9wcr+gmDSyh9I7zPdLtvzQAuJvSv/NncQtukuciet5hdqN86eXChZR2tnJh/CKbpOmFIsAX21m2oxCZ5cZpKM5Wsd/7KtFnlDJlwp9QnNXnTco7A9JUdPBX6PfuRDHKTBUzE4XuP1RneREYl5CMUTIOWM6hv3cj5TlTmgA0ojOErs5G1gILqKxEPH3QN63lwO9tA24mTPrtsqOafbG6og44DsXNfRtFAXwlUYnCcxTy9apF8X9fRN9ujDHGGGOMMcYYY4wxxpQ7PgdJnhrgWHT+MiL7b5vRecRy4J2E5DImURqB61GCzu7cPdZnf8en2qaquIDirvxuR5lijaloMsAN9Pxexo14WWwqmM/Rc+XIPZ+PXWpjYmAm2nCXqiDvoFA/xlQMGWAZpStH7lmGl1qmgjiT6JQj98yJ9QuqlJqkBagS5gV450cCvNOYRHiF6GeQlbF+QZXidWx4Mihubl3E790P9MYn7UHxEis8vYleOUBXZPsGeK9phxUkPPsIM8r/EdgT4L2mHVaQ8LyD8nhEzRocVDo4VpB4eCrAO58M8E7TCStIPCwO8M4fB3inMYlQh2JsRWXifY0wG39jEuMDRKcg749ZdmNi4TZKV47bY5famJioQ6naeqoc9+KllalwaoAvoPORQhVjL7oHYqOKqRomo9lkD90rxp7s70xOSMaqx75YyTMYOANFNTks+28bUVSTR4EdCclljDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGGGOMMcYYY4wxxhhjjDHGmKT4f/ZpkaGbZfaMAAAAAElFTkSuQmCC"
            },
        "causedSeqFailure": true,
        "additionalResults": [
              {
                "name": "Step Comment",
                "props": [
                  {
                    "name": "Step Comment",
                    "type": "String",
                    "flags": 8192,
                    "value": "fkeofke"
                  }
                ]
              }
            ]
        },
        {
            "id": 3,
            "group": "M",
            "stepType": "ET_MPFT",
            "name": "iLON_Set IP",
            "start": "2022-12-28T12:07:55.823+00:00",
            "status": "S",
            "errorCode": 0,
            "tsGuid": "ID#:26N9ivz6ckOEe+rIFbGNCA",
            "totTime": 2.2265791,
            "causedUUTFailure": false,
            "booleanMeas": [
              {
                "name": "name1",
                "status": "P"
              },
              {
                "name": "name2",
                "status": "S"
              },
              {
                "name": "name3",
                "status": "F"
              }
              ]
          },
          {
            "id": 4,
            "group": "M",
            "stepType": "NI_Wait",
            "name": "Wait for startup - 20sec",
            "start": "2022-12-28T12:07:11.91+00:00",
            "status": "D",
            "errorCode": 0,
            "tsGuid": "ID#:2ts0P6bg+ECRaHSpds964B",
            "totTime": 20.0358029,
            "causedUUTFailure": false
          },
        {
        "id": 5,
        "group": "C",
        "stepType": "WATS_SeqCall",
        "name": "Jig Power-up3",
        "status": "D",
        "chart": {
              "chartType": "Line",
              "label": "FR [Mic BA Inner]",
              "xLabel": "Lin",
              "xUnit": "Hz",
              "yLabel": "dB",
              "yUnit": "FS",
              "series": [
                {
                  "dataType": "XYG",
                  "name": "FR [Mic BA Inner]",
                  "xdata": "0;1;2;3",
                  "ydata": "0;1;2;3"
                },
                {
                  "dataType": "XYG",
                  "name": "FR Lower Limit (FR [Mic BA Inner])",
                  "xdata": "0;1;2;3",
                  "ydata": "0;2;4;6"
                },
                {
                  "dataType": "XYG",
                  "name": "FR Upper Limit (FR [Mic BA Inner])",
                  "xdata": "0;1;2;3",
                  "ydata": "0;3;6;9"
                }
              ]
            }
        }],
    "seqCall": {
      "path": "seq path",
      "name": "seq name",
      "version": "version_number"
    }
  },
  "uut": {
    "execTime": 142.1732307,
    "testSocketIndex": 32767,
    "batchSN": "1234567890",
    "comment": "I am a comment",
    "fixtureId": "1234567890",
    "user": "user",
    "batchFailCount": null,
    "batchLoopIndex": null
  },
  "miscInfos": [{"description": "test_item_1", "text": null, "numeric": 0},
                {"description": "test_item_2", "text": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "numeric": null}]
}"""

#
# import requests
# import json

# WATSTOKEN = 'dGVzdDoqazFRQTk5MnlZMUpZV0hwOWNLa2tZTDl4ODZ2OG8='
# request_url = 'https://akgre.wats.com/api/Report/WSJF'
# headers = {'Accept': 'application/json', 'Authorization': 'Basic ' + WATSTOKEN}
# response = requests.post(request_url, headers=headers, data=json.dumps(json.loads(json_data)), timeout=30)
#
# # response = requests.get('https://akgre.wats.com/api/Report/Wsjf/74dbbb17-392a-44f5-bb3a-d0e0a47cbc51', headers=headers, timeout=60)
#
# print(response.status_code)
# print(response.json())
#
# print("a" * 200)

# class UUTReportEnhanced(UUTReport):
#     type: Literal[ReportType.tuple()] = Field(ReportType.test, title='Type',
#                                               description='The type of report, T = Test, R = Repair')
#     id: UUID = Field(uuid.uuid4(), title='ID', description='A Globally Unique ID of the report. A report submitted with the '
#                                                   'same ID as another will overwrite the report. For the client if '
#                                                   'missing it will be generated but it must be supplied if uploaded '
#                                                   'using the swagger API. The valid format for a GUID is '
#                                                   '{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX} where X is a '
#                                                   'hex digit (0,1,2,3,4,5,6,7,8,9,A,B,C,D,E,F).')
#     result: Literal[ResultStatus.tuple()] = Field(None, title='Result',
#                                                   description='The result of the whole report. This must match the '
#                                                               'result of the first step in root.')
#     start: str = Field(datetime.datetime.now(), regex=r'^\d{2,4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}.\d{1,2}.{0,10}\+\d{1,2}:\d{1,2}',
#                        max_length=34, title='Local Start Time',
#                        description='The minimum requirement for this field is the data in the format YYYYMMDD, however,'
#                                    ' this model requires the full date time format. If the start date is in the '
#                                    'future the report will not be processed unit that time has passed... but should '
#                                    'we accept time travel in our testing?')
#     root: Step = Field(None)
#     uut: UUT = Field(None)
#
#     @root_validator()
#     def validate_root(cls, values):
#         print(values)
#         uut_values = {}
#         for key in values.keys():
#             if key in UUT.__fields__:
#                 uut_values[key] = values[key]
#         for key in uut_values.keys():
#             del values[key]
#         if uut_values:
#             values['uut'] = UUT(**uut_values)
#         return values
#
#     def add_uut(self, uut=None, **kwargs):
#         if kwargs:
#             self.uut = UUT(**kwargs)
#         else:
#             self.uut = uut
#
#     class Config:
#         extra = 'allow'
#
#
# test_report = UUTReportEnhanced(pn='abc', sn='123', rev='8', processCode=1100, machineName='a',
#                                 location='here', purpose='stuff', user='bob', testSocketIndex=-1, fixtureId='1245')
# # report_header.add_uut(user='bob')
#
# main = MainStep
#
# print(test_report.json(indent=2))
