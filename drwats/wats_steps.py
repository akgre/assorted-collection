from __future__ import annotations
from decimal import Decimal
from typing import Optional, List, Literal, Union
from itertools import count
from pydantic import BaseModel, validator, root_validator, ValidationError, Field
from pydantic.error_wrappers import ErrorWrapper

from src.drwats.wats_enums import ReportType, StepGroup, \
    StepType, ResultStatus, MeasureStatus, StepStatus, \
    StringCompOp, NumericCompOp, ChartTypes
from src.drwats.wats_measure import PassFail, StringValue, NumericLimit


class LoopInfo(BaseModel):
    idx: int = Field(None)
    num: int
    endingIndex: int
    passed: int
    failed: int


class Attachment(BaseModel):
    """
    Attachments such as README, Photos, etc.
    Attachments can be included in a step by adding an Attachment object to a step. WSJF uses Base64
    encoded contents to attach a file.
    Can't be used in the same step as a chart.

    Example:
    "attachment": {
        "name": "WiFiNotification",
        "contentType": "image/png",
        "data": "iVBORw0KGgoAAAANSUhEUgAA...(continue data)"
    }
    """
    name: str = Field(..., min_length=1, max_length=100, title='Name', description='The name of the attachment')
    contentType: str = Field(..., min_length=1, max_length=100, title='Content Type',
                             description='The Mime-type of the attachment. Examples: <image/bmp>, <application/json>, '
                                         '<application/xml>')
    data: str = Field(..., title='Data', description='A base64 encoded string of the contents of the file.')


class ChartSeries(BaseModel):
    dataType: Literal['XYG'] = Field(...)
    name: str = Field(..., min_length=1, max_length=100)
    xdata: str = Field(..., regex=r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:;[+-]?(?:\d+(?:\.\d*)?|\.\d+))*$')
    ydata: str = Field(..., regex=r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:;[+-]?(?:\d+(?:\.\d*)?|\.\d+))*$')

    @validator('xdata')
    def check_x_entries_count(cls, value, values):
        # check if all the required values are assigned, if not then return will show missing values
        if set(values.keys()) != set(['dataType', 'name']):
            return values

        if len(value.split(';')) > 10_000:
            raise ValueError(f'x data can’t have more than 10,000 entries -> x: {len(value.split(";"))}')

        return value

    @validator('ydata')
    def check_y_entries_count(cls, value, values):
        # check if all the required values are assigned, if not then return will show missing values
        if set(values.keys()) != set(['dataType', 'name', 'xdata']):
            return values

        if len(value.split(';')) != len(values['xdata'].split(';')):
            raise ValueError(f'The number of entries for x and y data do not match '
                             f'-> x: {len(values["xdata"].split(";"))}, y: {len(value.split(";"))}')

        if len(value.split(';')) > 10_000:
            raise ValueError(f'y data can’t have more than 10,000 entries -> y: {len(value.split(";"))}')

        return value


class Chart(BaseModel):
    chartType: Literal[ChartTypes.tuple()] = Field(...)
    label: str = Field(..., min_length=1, max_length=100)
    xLabel: str = Field(..., min_length=1, max_length=50)
    xUnit: str = Field(..., min_length=1, max_length=20)
    yLabel: str = Field(..., min_length=1, max_length=50)
    yUnit: str = Field(..., min_length=1, max_length=20)
    series: Optional[List[ChartSeries]]

    @validator('series')
    def check_series_limit(cls, value):
        if len(value) > 10:
            raise ValueError(f"Chart can not have more than 10 series: Series count: {len(value)}")
        return value


class SeqCall(BaseModel):
    """
    Sequence steps are steps which contains a sequence call. Sequence calls are used to create hierarchy structured
    data.
    Example:
    "seqCall": {
        "path": "Z:\\Test and Demo\\FAT-SAT\\TS2016\\SeqFiles\\TS2016 - FATv1.seq",
        "name": "NI steps",
        "version": "1.0.1"
    }
    """
    path: str = Field(..., min_length=1, max_length=500)
    name: str = Field(..., min_length=1, max_length=200)
    version: str = Field(..., min_length=1, max_length=30)


class MessagePopup(BaseModel):
    """
    Properties   	Data type       Required
    button          Number	        Yes
    buttonFormat	String	        No
    response	    String (200)	Yes
    """
    button: int = Field(..., ge=-32_768, le=32_767, title='Button Index',
                        description='Index number of the button on the popup. Negative values could be used to indicate'
                                    'an error.')
    buttonFormat: str = Field(None)
    response: str = Field(..., min_length=1, max_length=100, title='Response',
                          description='Response from the popup. Documentation stats a limit of 200, after testing it '
                                      'will only accept 100 and when displaying only 70 are visible. to avoid this use '
                                      'new line characters.')


class CallExe(BaseModel):
    """
    In general, an exit code of 0 indicates that the program completed successfully without any errors,
    while a non-zero exit code indicates that an error occurred. The exact meaning of non-zero exit codes can vary
    depending on the program or operating system.

    Properties   	Data type   Required
    exitCode	    Number	    Yes
    exitCodeFormat	String	    No
    """
    exitCode: int = Field(...)
    exitCodeFormat: str = Field(None)


class Step(BaseModel):
    """
    Properties	            Data type                   Required
    group	                Character (S, M, C)	        Yes
    name	                String (100)	            Yes
    status	                Character (P, F, E, T, S)   Yes
    stepType	            String	                    Yes
    id	                    Number	                    If on one step, required for all
    interactiveExeNum	    Number	                    No
    interactiveExeNumFormat String	                    No
    reportText	            String	                    No
    start	                DateTime	                No
    causedSeqFailure  	    Bool	                    No
    causedUUTFailure	    Bool	                    No
    errorCode	            Number	                    No
    errorCodeFormat	        Number	                    No
    errorMessage	        String	                    No
    totTime	                Number	                    No
    totTimeFormat	        Number	                    No
    tsGuid	                String (30)	                No
    seqCall	                seqCall object	            No
    numericMeas	            Array of numericMeas	    No
    stringMeas	            Array of stringMeas	        No
    booleanMeas	            Array of booleanMeas	    No
    chart	                chart object	            No
    attachment	            attachment object	        No
    loop	                loopInfo object	            No
    steps	                step object	                No
    callExe	                callExe object	            No
    messagePopup	        messagePopup object	        No

    Validation Rules
    - The first step's status is required to match report status and have a seqCall. The root property of the root
      object contains the actual test data. It is the root step of the step hierarchy and must therefore only contain
      a sequence call.
    - id is required to be unique.
    - At least one of seqCall, numericMeas, stringMeas, booleanMeas, chart, attachment or additionalResults is required.
    - Can only have one of seqCall, numericMeas, stringMeas, or booleanMeas.
    - step can only have value if seqCall also has value, and at least one step is required if seqCall has value.
    - Can only have one of chart or attachment.
    - If one numericMeas, stringMeas, or booleanMeas; status and numericMeas, stringMeas, or booleanMeas status is
      required to match.
    - If multiple numericMeas, stringMeas, or booleanMeas; status cannot be F unless at least one of the numericMeas,
      stringMeas, or booleanMeas have status F.
    - If multiple numericMeas, stringMeas, or booleanMeas, status cannot be P unless none of the numericMeas,
      stringMeas, or booleanMeas have status F.
    - numericMeas, stringMeas, or booleanMeas name is required be unique within a step.
    - step name within a step is required to be unique.
    - If status is S (Skipped), numericMeas, stringMeas, booleanMeas, callExe, messagePopup, chart, attachment,
      additionalResults and steps will be ignored. This provides better analysis of skipped steps.
    - stepType is the icon displayed in WATS. Possible values: SequenceCall, NumericLimitTest, ET_NLT, ET_MNLT,
      StringValueTest, ET_SVT, ET_MSVT, PassFailTest, ET_PFT, ET_MPFT, Action, ET_A, Label, CallExecutable,
      MessagePopup.
    """
    count: int = Field(default_factory=count().__next__, init=False, exclude=True)
    id: int = Field(..., ge=0)
    group: Literal[StepGroup.tuple()] = Field(...)
    stepType: Literal[StepType.tuple()] = Field(...)
    loop: Optional[LoopInfo]  # TBD
    name: str = Field(..., min_length=1, max_length=100)
    start: str = Field(None,
                       regex=r'^(\d{2,4}-\d{1,2}-\d{1,2})(T\d{2}:\d{2}:\d{2}(\.\d{1,10})?(Z|[+-]\d{1,2}:?\d{2})?)?$',
                       # r'^\d{2,4}-\d{1,2}-\d{1,2}T\d{1,2}:\d{1,2}:\d{1,2}.\d{1,2}.{0,10}\+\d{1,2}:\d{1,2}$',
                       title='Start', description='The time specified should be local time.'
                                                  'The minimum requirement for this field is the data in the format '
                                                  'YYYYMMDD, however, this model requires the full date time format. '
                                                  'If the start date is in the future the report will not be '
                                                  'processed unit that time has passed... but should we accept time '
                                                  'travel in our testing?')
    status: Literal[StepStatus.tuple()] = Field(..., title='Status',
                                                description='The first status must match the report result. Any '
                                                            'sub-step doesn\'t require matching statuses. If there is '
                                                            'a measurement in the step then the step and measurement '
                                                            'must match. '
                                                            'Can not be Error or Terminated if there is a measurement. '
                                                            'This is because the measurement status must match the '
                                                            'step status. Measurements can only be P,F,S. if there is '
                                                            'an error the measurement should be excluded.')
    errorCode: int = Field(None, ge=-2_147_483_648, le=2_147_483_647, title='Error Code',
                           description='See description of report error code. The error code will only be displayed in '
                                       'a step if there is also an error message. If there is an error message and no '
                                       'error code it will show the code as "undefined" in the report. The error code '
                                       'and error message are independent from the status. The test/system designer '
                                       'will need to validate if the error code causes the step to error.')
    errorMessage: str = Field(None, min_length=1, max_length=200, title='Error Message',
                              description='See description of report error message. The error message will only be '
                                          'displayed is there is text; only white space charters will be ignored. '
                                          'The error code and error message are independent from the status. The '
                                          'test/system designer will need to validate if the error code causes the '
                                          'step to error. '
                                          'In the report the message is above the step dropdown')
    tsGuid: str = Field(None, max_length=30, title='Step UUID',
                        description='The step-id parameter specifies the identifier of the desired test step. This is '
                                    'different to a "execution id" (which is not used by WATS).'
                                    'Not displayed in a report. This is a string with the maximum length of 30 '
                                    'characters; WATS does not perform and checks on this field. '
                                    'If you have a system like DOORS then you can place the step ID here. For general '
                                    'scripts the versioning can be entered into the sequence call field.'
                                    'The TestStand Sequence Editor assigns a Unique Step ID to each step added to a '
                                    'sequence. Unique Step ID, which is a GUID represented as a string that begins '
                                    'with “ID#:” and contains 26 characters (only alphanumeric characters and the '
                                    'special characters “#,” “ :,” “+,” and “/”). TestStand attempts to maintain '
                                    'globally unique step IDs. '
                                    'If used in python the user must manage this themself.')
    totTime: Decimal = Field(None, ge=0, title='Execution Time',
                             description='[OPTIONAL] The total time in second to complete the step. '
                                         'Although a negative value can be entered into the API the DrWATS '
                                         'model will only accept a value greater or equal to 0. Note: Limit '
                                         'is more than a googol (1×10^308)')
    causedSeqFailure: bool = Field(None, title='Step Caused Sequence Failure',
                                   description='When the report is processed it will trigger UUT Failure to also be '
                                               'true and display as it the UUT had failed. The preference seems to be '
                                               'to use causedUUTFailure (TBC).')
    causedUUTFailure: bool = Field(None, title='Step Caused UUT Failure',
                                   description='If causedUUTFailure is True then the report will highlight the step '
                                               'which has this and make a link to quick jump to the step. When the'
                                               'report is processed it will also update stepIdCausedUUTFailure.'
                                               'The message that is given is dependant on the result of the report '
                                               'not the step status. '
                                               'Failed will say "Step caused UUT Failed", Terminated will say '
                                               '"Step caused UUT Terminated". If the report result is passed the '
                                               'upload will work but the report will state "Step caused UUT Passed", '
                                               'however, this is a state that should not be allowed. '
                                               'The state of the step should also match the Report result if '
                                               'UUT failure is true as this should end the test. If there happens to '
                                               'be more than one step that has UUT failure then then only the first '
                                               'will be highlight. It is up to the test/system designer to classify '
                                               'what is regarded as a failure of the UUT.')
    additionalResults: str = Field(None, title='Additional Results',
                                   description='This will add a chart of information to a step in the same format of '
                                               'additional data. Properties are allowed to have sub properties and '
                                               'will display extra dropdowns to display the information. This can be '
                                               'any text.')
    reportText: str = Field(None, min_length=1, max_length=5000, title='Step Comment',
                            description='Can be any text. Has been tested to accept more than 5000 characters, however,'
                                        ' this will be printed on a single line so when displaying the user will only '
                                        'see around 160. To avoid this use new line characters.'
                                        'In the report the comment is above the step dropdown.')
    messagePopup: MessagePopup = Field(None, title='Message Popup',
                                       description='Message popup is used when a pop-up message is displayed. '
                                                   'Contains a button number and a response text in the step dropdown. '
                                                   'If the stepType MessagePopup is used it will display a message '
                                                   'icon in the report. '
                                                   'Can not be used in combination with Boolean, String, Numeric or '
                                                   'Call Exe')
    booleanMeas: List[PassFail] = Field(None, title='Boolean Measurement',
                                        description='Single Measurement: When there is a single measurement the status '
                                                    'of the measurement must match the status of the step. If the '
                                                    'status is skipped then the step will not show the boolean value. '
                                                    'In this skipped state the step dropdown is removed and the user '
                                                    'won\'t have access to the attachment, additionalResult or chart. '
                                                    'Multiple Measurement: For multiple measurements the system needs '
                                                    'to be able to tell the statuses apart, therefore, they must all '
                                                    'have unique names. If there is a single failure then the step '
                                                    'status must also be fail. If step status is S (Skipped), the '
                                                    'results will be ignored. This provides better analysis of '
                                                    'skipped steps. '
                                                    'Can not be used in combination with combination with '
                                                    'Numeric, String, seq call, '
                                                    'call exe or Message Popup.')
    stringMeas: List[StringValue] = Field(None, title='String Measurement',
                                          description='Single Measurement: When there is a single measurement the '
                                                      'status '
                                                      'of the measurement must match the status of the step. If the '
                                                      'status is skipped then the step will not show the string '
                                                      'value. '
                                                      'In this skipped state the step dropdown is removed and the user '
                                                      'won\'t have access to the attachment, additionalResult or '
                                                      'chart. '
                                                      'Multiple Measurement: For multiple measurements the system '
                                                      'needs '
                                                      'to be able to tell the statuses apart, therefore, they must all '
                                                      'have unique names. If there is a single failure then the step '
                                                      'status must also be fail. If step status is S (Skipped), the '
                                                      'results will be ignored. This provides better analysis of '
                                                      'skipped steps. '
                                                      'Can not be used in combination with combination with '
                                                      'Boolean, Numeric, seq call,'
                                                      'call exe or Message Popup')
    numericMeas: List[NumericLimit] = Field(None, title='Numeric Measurement',
                                            description='Single Measurement: When there is a single measurement the '
                                                        'status '
                                                        'of the measurement must match the status of the step. If the '
                                                        'status is skipped then the step will not show the numeric '
                                                        'value. '
                                                        'In this skipped state the step dropdown is removed and the '
                                                        'user '
                                                        'won\'t have access to the attachment, additionalResult or '
                                                        'chart. '
                                                        'Multiple Measurement: For multiple measurements the system '
                                                        'needs '
                                                        'to be able to tell the statuses apart, therefore, they must '
                                                        'all '
                                                        'have unique names. If there is a single failure then the step '
                                                        'status must also be fail. If step status is S (Skipped), the '
                                                        'results will be ignored. This provides better analysis of '
                                                        'skipped steps. '
                                                        'Can not be used in combination with combination with '
                                                        'Boolean, String, seq call,'
                                                        'call exe or Message Popup')
    callExe: CallExe = Field(None, title='Call Executable',
                             description='Step which contains a reference to an executable. Use "CallExecutable" in '
                                         'stepType to get the corresponding step icon. '
                                         'Can not be used in combination with combination with Boolean, String, '
                                         'Numeric or Message Popup')
    seqCall: SeqCall = Field(None, title='Sequence Call',
                             description='Sequence steps are steps which contains a sequence call. Sequence calls are '
                                         'used to create hierarchy structured data. Step can only have value if '
                                         'seqCall also has value, and at least one step is required if seqCall has '
                                         'value; though when tested in the API steps is allowed to be missing. This '
                                         'model will raise an error. '
                                         'Can not be used in combination with combination with Boolean, String, '
                                         'Numeric, Call Exe or Message Popup. '
                                         'A sequence step can have an attachment, additionalResult or chart')
    steps: List[Step] = Field(None, title='Steps',
                              description='Creates a list of steps. Step can only have value if '
                                          'seqCall also has value, and at least one step is required if seqCall has '
                                          'value; though when tested in the API steps is allowed to be missing. This '
                                          'model will raise an error. '
                                          'The API will accept steps as a blank list but this model will error.'
                                          'Sub-steps can have the same name as a parent. Only steps on the same level '
                                          'need to be unique. '
                                          'The status of the sub-step and parent don\'t have to match and does not get '
                                          'validated. The occurs on the first step with result and steps with '
                                          'measurements')
    chart: Chart = Field(None, title='Chart',
                         description='A chart can be added to any step but can not be used with attachment at the same '
                                     'time. The WATS report will accept a chart with only 1 value but this won\'t '
                                     'display anything in the chart area as currently only line graphs are '
                                     'implemented. A chart can only have up to 10 series and each series can only have '
                                     'up to 10,000 data points. No evaluation is done on chart so the implementation '
                                     'of limit lines must be processed by the system/test. Charts from multiple tests '
                                     'can be evaluated, however, when looking at Test step yield & analysis for an '
                                     'overview it is a great benefit to add values which will show in a spot check as '
                                     'looking through all charts can take a long time to analyse')
    attachment: Attachment = Field(None, title='Attachment',
                                   description='This will add a downloadable file from a link under the dropdown '
                                               'of the step. '
                                               'Attachment can not be used with the chart in the same step'
                                               'If status is S (Skipped), attachment, will be ignored. This provides '
                                               'better analysis of skipped steps.')

    @validator('id')
    def validate_id(cls, value, values):
        print('id', value, values['count'])
        if value != values['count']:
            raise ValueError(f'Step ID does not match the order of steps: got id={value}, expected {values["count"]}')
        return value

    @validator('causedUUTFailure')
    def validate_causedUUTFailure(cls, value, values):
        if not values.get('status'):
            ValueError(f'Unable to evaluate causedUUTFailure as step has no valid status')
        elif value and (values['status'] == StepStatus.PASSED):
            raise ValueError(f'Step status can not be Passed if step caused UUT failure.')
        elif value and (values['status'] == StepStatus.DONE):
            raise ValueError(f'Step status can not be Done if step caused UUT failure.')
        elif value and (values['status'] == StepStatus.SKIPPED):
            raise ValueError(f'Step status can not be Skipped if step caused UUT failure.')
        return value

    @validator('booleanMeas')
    def validate_booleanMeas(cls, value, values):
        # print('booleanMeas', len(value))
        if values.get('messagePopup'):
            raise ValueError('messagePopup and booleanMeas can not be used in the same step.')
        if not values.get('status'):
            raise ValueError(f'Unable to evaluate booleanMeas as step has no valid status')
        # if values['status'] == StepStatus.SKIPPED:
        #     value = None
        errors = []
        for i, measure_status in enumerate([measure.status for measure in value]):
            if values['status'] in [StepStatus.PASSED, StepStatus.FAILED]:
                if measure_status == MeasureStatus.SKIPPED:
                    continue
                elif values['status'] != measure_status:
                    errors += [ErrorWrapper(
                        ValueError(f'Step status and measurement status do not match. Index: {i}'), loc=(i, "status",))]
        if len(value) > 1:
            # here i need to raise multiple errors depending if there are many missing
            list_of_all_names = [measure.name for measure in value]
            seen = set()
            dupes = [x for x in list_of_all_names if x in seen or seen.add(x)]
            print(list_of_all_names, dupes)
            for i, measure_name in enumerate([measure.name for measure in value]):
                if not measure_name:
                    errors += [ErrorWrapper(
                        ValueError(f'Names can not be None for multiple measurements. Index: {i}'),
                        loc=(i, "name",))]
                elif measure_name in dupes:
                    errors += [ErrorWrapper(
                        ValueError(f'All the names must be unique for multiple measurements. '
                                   f'Index: {i}, Name: {measure_name}'),
                        loc=(i, "name",))]
        if errors:
            raise ValidationError(errors, model=cls)
        return value

    @validator('stringMeas')
    def validate_stringMeas(cls, value, values):
        # print('stringMeas', len(value))
        additional_step_object = next(filter(lambda x: x is not None,
                                             [x for x in ['messagePopup', 'booleanMeas'] if values.get(x)]), None)
        if additional_step_object:
            print(additional_step_object)
            raise ValueError(f'{additional_step_object} and numericMeas can not be used in the same step.')

        if not values.get('status'):
            raise ValueError(f'Unable to evaluate stringMeas as step has no valid status')
        # if values['status'] == StepStatus.SKIPPED:
        #     value = None
        errors = []
        for i, measure_status in enumerate([measure.status for measure in value]):
            if values['status'] in [StepStatus.PASSED, StepStatus.FAILED]:
                if measure_status == MeasureStatus.SKIPPED:
                    continue
                elif values['status'] != measure_status:
                    errors += [ErrorWrapper(
                        ValueError(f'Step status and measurement status do not match. Index: {i}'), loc=(i, "status",))]
        if len(value) > 1:
            # here i need to raise multiple errors depending if there are many missing
            list_of_all_names = [measure.name for measure in value]
            seen = set()
            dupes = [x for x in list_of_all_names if x in seen or seen.add(x)]
            print(list_of_all_names, dupes)
            for i, measure_name in enumerate([measure.name for measure in value]):
                if not measure_name:
                    errors += [ErrorWrapper(
                        ValueError(f'Names can not be None for multiple measurements. Index: {i}'),
                        loc=(i, "name",))]
                elif measure_name in dupes:
                    errors += [ErrorWrapper(
                        ValueError(f'All the names must be unique for multiple measurements. '
                                   f'Index: {i}, Name: {measure_name}'),
                        loc=(i, "name",))]
        if errors:
            raise ValidationError(errors, model=cls)
        return value

    @validator('numericMeas')
    def validate_numericMeas(cls, value, values):
        # print('numericMeas', len(value), value)
        additional_step_object = next(filter(lambda x: x is not None,
                                             [x for x in ['messagePopup', 'booleanMeas', 'stringMeas'] if
                                              values.get(x)]), None)
        if additional_step_object:
            print(additional_step_object)
            raise ValueError(f'{additional_step_object} and numericMeas can not be used in the same step.')
        if not values.get('status'):
            raise ValueError(f'Unable to evaluate numericMeas as step has no valid status')
        # if values['status'] == StepStatus.SKIPPED:
        #     value = None
        errors = []  # here we need to raise multiple errors
        for i, measure_status in enumerate([measure.status for measure in value]):
            if values['status'] in [StepStatus.PASSED, StepStatus.FAILED]:
                if measure_status == MeasureStatus.SKIPPED:
                    continue
                elif values['status'] != measure_status:
                    errors += [ErrorWrapper(
                        ValueError(f'Step status and measurement status do not match. Index: {i}'), loc=(i, "status",))]

        if len(value) > 1:
            list_of_all_names = [measure.name for measure in value]
            seen = set()
            dupes = [x for x in list_of_all_names if x in seen or seen.add(x)]
            print(list_of_all_names, dupes)
            for i, measure_name in enumerate([measure.name for measure in value]):
                if not measure_name:
                    errors += [ErrorWrapper(
                        ValueError(f'Names can not be None for multiple measurements. Index: {i}'),
                        loc=(i, "name",))]
                elif measure_name in dupes:
                    errors += [ErrorWrapper(
                        ValueError(f'All the names must be unique for multiple measurements. '
                                   f'Index: {i}, Name: {measure_name}'),
                        loc=(i, "name",))]
        if errors:
            raise ValidationError(errors, model=cls)
        return value

    @validator('callExe')
    def validate_callExe(cls, value, values):
        # print('callExe', value)
        additional_step_object = next(filter(lambda x: x is not None,
                                             [x for x in ['messagePopup', 'booleanMeas', 'stringMeas', 'numericMeas']
                                              if values.get(x)]), None)
        if additional_step_object:
            # print(additional_step_object)
            raise ValueError(f'{additional_step_object} and callExe can not be used in the same step.')
        return value

    @validator('seqCall')
    def validate_seqCall(cls, value, values):
        # print('seqCall', value)
        additional_step_object = next(filter(lambda x: x is not None,
                                             [x for x in
                                              ['messagePopup', 'booleanMeas', 'stringMeas', 'numericMeas', 'callExe']
                                              if values.get(x)]), None)
        if additional_step_object:
            # print(additional_step_object)
            raise ValueError(f'{additional_step_object} and seqCall can not be used in the same step.')
        return value

    @validator('steps')
    def validate_steps(cls, value, values):
        # print('steps', len(value))
        # for x in value:
        # print(x.id)
        if not values.get('seqCall'):
            raise ValueError(f'step can only have value if seqCall also has value')
        # if len(value) > 1:
        #     list_of_all_names = [step.name for step in value]
        #     if len(list_of_all_names) > len(set(list_of_all_names)):
        #         seen = set()
        #         dupes = [x for x in list_of_all_names if x in seen or seen.add(x)]
        #         print(list_of_all_names, dupes)
        #         raise ValueError(f'{dupes} All step names within a step are required to be unique.')
        errors = []  # here we need to raise multiple errors
        if len(value) > 1:
            list_of_all_names = [measure.name for measure in value]
            seen = set()
            dupes = [x for x in list_of_all_names if x in seen or seen.add(x)]
            print(list_of_all_names, dupes)
            for i, measure_name in enumerate([measure.name for measure in value]):
                if measure_name in dupes:
                    errors += [ErrorWrapper(
                        ValueError(f'All step names within a step are required to be unique. '
                                   f'Index: {i}, Name: {measure_name}'),
                        loc=(i, "name",))]
        if errors:
            raise ValidationError(errors, model=cls)
        return value

    @validator('attachment')
    def validate_attachment(cls, value, values):
        if not values.get('chart'):
            raise ValueError('Chart and Attachment can not be used in the same step.')
        return value

    @root_validator
    def validate_step_rules(cls, step_values):
        print("validate_step_rules", step_values)
        # if set(step_values.keys()) != set(['id', 'group', 'stepType', 'name', 'status']):
        #     return step_values
        if not step_values.get('status'):
            raise ValueError(f'Unable to evaluate step id={step_values["id"]} as step has no valid status')

        missing = list(sorted(set(Step.__fields__.keys()) - set(step_values.keys())))
        print("missing", step_values['id'], missing)
        if missing:
            if missing == ['steps']:
                # In the WSJF and WSXF the status of a sequence call step is independent of the status of the sub-steps.
                # Steps are only evaluated if they are 'booleanMeas', 'stringMeas' or 'numericMeas'
                # Therefor the evaluation of a sequence call is determined by the system/test designer.
                return step_values
            raise ValidationError(
                [ErrorWrapper(
                    ValueError(f'Unable to evaluate step id={step_values["id"]} with invalid fields: {missing}'),
                    loc=("status",))], model=cls)
        #
        # missing = list(sorted(set(['messagePopup', 'booleanMeas', 'stringMeas', 'numericMeas', 'callExe', 'seqCall']) - set(step_values.keys())))
        # if missing:
        #     raise ValueError(f'Unable to evaluate string measure with invalid fields: {missing}')

        return step_values


steps = {
    "id": 0,
    "group": "M",
    "stepType": "WATS_SeqCall",
    "name": "DALI Test",
    "start": "2022-12-28T12:08:39.403+00:00",
    "status": "P",
    "errorCode": 0,
    "tsGuid": "ID#:rp4VxXceHEyCbPnwhRwHID",
    "totTime": 21.5818178,
    "causedUUTFailure": False,
    "steps": [{"id": 1,
               "group": "M",
               "stepType": "ET_NLT",
               "name": "VA",
               "start": "2022-12-28T12:07:11.483+00:00",
               "status": "P",
               "errorCode": 0,
               "tsGuid": "ID#:q25e2K/0a0eF04mnKNOSzC",
               "totTime": 0.3233067,
               "causedUUTFailure": False,
               "reportText": "I am a comment",
               "numericMeas": [
                   {
                       "compOp": "GELE",
                       "name": None,
                       "status": "F",
                       "unit": "volt",
                       "value": 17.879107705605,
                       "highLimit": 16,
                       "lowLimit": 14
                   }],
               "chart": {"chartType": "Line",
                         "label": "i am a chart",
                         "xLabel": "x axis",
                         "xUnit": "time",
                         "yLabel": "y axis",
                         "yUnit": "No of jokes",
                         "series": [{"dataType": "XYG",
                                     "name": "PlotName 0",
                                     "xdata": "0;1;2;3",
                                     "ydata": "0.505966492022607;0.64645051547995;0.639659061179134;0.911752170787661"
                                     },
                                    {"dataType": "XYG",
                                     "name": "PlotName 1",
                                     "xdata": "0;1;2;3",
                                     "ydata": "0.205966492022607;0.74645051547995;0.539659061179134;0.211752170787661"
                                     }
                                    ]
                         }
               },
              {
                  "id": 2,
                  "group": "M",
                  "stepType": "WATS_SeqCall",
                  "name": "Power-On test",
                  "start": "2022-12-28T12:07:11.363+00:00",
                  "status": "P",
                  "errorCode": 0,
                  "tsGuid": "ID#:0u07T0pyr0S707rp7pTJtB",
                  "totTime": 44.2395103,
                  "causedUUTFailure": False,
                  "steps": [
                      {
                          "id": 3,
                          "group": "M",
                          "stepType": "ET_NLT",
                          "name": "VA",
                          "start": "2022-12-28T12:07:11.483+00:00",
                          "status": "P",
                          "errorCode": 0,
                          "tsGuid": "ID#:q25e2K/0a0eF04mnKNOSzC",
                          "totTime": 0.3233067,
                          "causedUUTFailure": False,
                          "numericMeas": [
                              {
                                  "compOp": "GELE",
                                  "name": None,
                                  "unit": "volt",
                                  "value": 14.879107705605,
                                  "highLimit": 16,
                                  "lowLimit": 14
                              }
                          ]
                      },
                      {
                          "id": 4,
                          "group": "M",
                          "stepType": "ET_NLT",
                          "name": "5V",
                          "start": "2022-12-28T12:07:11.843+00:00",
                          "status": "P",
                          "errorCode": 0,
                          "tsGuid": "ID#:JFFK1BNV6EaGCtbsJgn7fB",
                          "totTime": 0.061552,
                          "causedUUTFailure": False,
                          "numericMeas": [
                              {
                                  "compOp": "GELE",
                                  "name": None,
                                  "status": "P",
                                  "unit": "volt",
                                  "value": 5.08788365708408,
                                  "highLimit": 5.2,
                                  "lowLimit": 4.85
                              }
                          ]
                      },
                      {
                          "id": 5,
                          "group": "M",
                          "stepType": "NI_Wait",
                          "name": "Wait for startup - 20sec (1)",
                          "start": "2022-12-28T12:07:11.91+00:00",
                          "status": "D",
                          "errorCode": 0,
                          "tsGuid": "ID#:2ts0P6bg+ECRaHSpds964B",
                          "totTime": 20.0358029,
                          "causedUUTFailure": False
                      },
                      {
                          "id": 6,
                          "group": "M",
                          "stepType": "NI_Wait",
                          "name": "Wait for startup - 20sec (2)",
                          "start": "2022-12-28T12:07:11.91+00:00",
                          "status": "D",
                          "errorCode": 0,
                          "tsGuid": "ID#:2ts0P6bg+ECRaHSpds964B",
                          "totTime": 20.0358029,
                          "causedUUTFailure": False
                      }
                  ],
                  "seqCall": {
                      "path": "seq path",
                      "name": "seq name",
                      "version": "version_number"
                  }
              },
              {
                  "id": 7,
                  "group": "M",
                  "stepType": "ET_MNLT",
                  "name": "Test IO2 - Read back High",
                  "start": "2022-12-28T12:08:36.317+00:00",
                  "status": "P",
                  "errorCode": 0,
                  "tsGuid": "ID#:nMEuNcP/90WmmoKD/P911C",
                  "totTime": 0.2007856,
                  "causedUUTFailure": False,
                  "numericMeas": [
                      {
                          "name": "name1",
                          "unit": "volt",
                          "value": 6.09464961727265,
                          "highLimit": 5.5,
                          "lowLimit": 4
                      },
                      {
                          "compOp": "GELE",
                          "name": "name2",
                          "status": "P",
                          "unit": "volt",
                          "value": 5.09464961727265,
                          "highLimit": 5.5,
                          "lowLimit": 4
                      }
                  ]
              }
              ],
    "seqCall": {
        "path": "seq path",
        "name": "seq name",
        "version": "version_number"
    }
}

# try:
#     m = Step(**steps)
#     print(m.json(indent=2))
# except ValidationError as e:
#     from types import SimpleNamespace
#     for i, error in enumerate([SimpleNamespace(**error) for error in e.errors()], start=1):
#         print(f"{i:<2} {error.type:<28} | {str(error.loc):<55} | {error.msg}")
