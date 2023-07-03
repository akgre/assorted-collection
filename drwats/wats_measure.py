from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, validator, root_validator, Field, ValidationError
from pydantic.error_wrappers import ErrorWrapper

from src.drwats.wats_enums import MeasureStatus, StringCompOp, NumericCompOp


class PassFail(BaseModel):
    """
    This is the standard WATS pass-fail test which only contains a name and status
    - BooleanMeas is a measurement, where the measurement is true or false.
    """
    name: str = Field(None, max_length=100)
    status: Literal[MeasureStatus.tuple()] = Field(...)


class PassFailEnhanced(PassFail):
    """
    A Pass fail test only contains a name and a status. However, the string and numeric tests also contain a value.
    In this case I think it would be beneficial for pass-fail to have a value in some cases (like if you were looping
    over all tests to find all values)

    This means that value should be passive and only accessed directly from the model. When exporting the json for
    uploading to WATS it should be excluded.

    The standard class will only take the status <F, P>, however, this class has been enhanced to accept int <0, 1>,
    bool <False, True> or string <f, p> as inputs and coerce them to the values <F, P>.
    """
    value: Literal[MeasureStatus.tuple()] = Field(None, exclude=True)

    @root_validator(pre=True)
    def validate_pft_values(cls, pft_values):
        """
        This function takes a dictionary pft_values as input and modifies it in place to ensure that the status and
        value keys have consistent and valid values.

        If both value and status are None, the original dictionary is returned. This then shows an error handled by
        the class

        If status is not None, value is set to the value of status, and if value is not None, status is set
        to the value of value.

        If status is a boolean or integer, it is converted to a string indicating the measure
        status (passed or failed).

        Finally, the status string is converted to uppercase, and value is set to the same
        value as status. The modified dictionary is returned.

        This means that the user is allowed to set the status by setting an int <0, 1>, bool <False, True> or
        string <f, p> and it will be corrected to the valid values of <F, P> (Failed and Passed). Anything else will be
        seen as an invalid value for WATS.

        :param pft_values:
        :return:
        """
        if pft_values.get('value', None) is None and pft_values.get('status', None) is None:
            return pft_values

        if pft_values.get('status') is not None:
            pft_values['value'] = pft_values['status']
        elif pft_values.get('value') is not None:
            pft_values['status'] = pft_values['value']

        if isinstance(pft_values['status'], bool) or isinstance(pft_values['status'], int):
            pft_values['status'] = (MeasureStatus.FAILED, MeasureStatus.PASSED)[pft_values['status']]

        if not isinstance(pft_values['status'], str):
            return

        pft_values['status'] = pft_values['status'].upper()
        pft_values['value'] = pft_values['status']

        return pft_values


class StringValue(BaseModel):
    """
    Used to log string value test data. The required fields are CompOperator, String Value
    and Status. Name must be present for multiple tests, but not for a single test.
    - stringMeas is a measurement, where the measurement is text.
    Properties  	Data type	                                Required
    compOp	        Enum (LOG, EQ, NE, CASESENSIT, IGNORECASE)	Yes
    limit	        String (100)	                            If compOp is single limit, yes
    value	        String (100)	                            Yes
    name	        String (100)	                            If multiple stringMeas, yes
    status	        Character (P, F, S)	                        Yes
    """
    compOp: Literal[StringCompOp.tuple()] = Field(...)
    name: str = Field(None, min_length=1, max_length=100)
    status: Literal[MeasureStatus.tuple()] = Field(...)
    value: str = Field(..., max_length=100)
    limit: str = Field(None, max_length=100)

    @validator('limit', always=True)
    def validate_limit(cls, value, values):
        """
        This function checks if the limit value is required

        If the other values have not been set then there are missing values, returning will show these values in the
        error message

        If status is set to skipped then the limit isn't validated

        If compOp is LOG then the limit isn't validated and the limit should be None

        Otherwise, there should be a limit, if not, then raise an error.

        :param value:
        :param values:
        :return:
        """
        # print("validate_limit", values)
        # check if all the required values are assigned, if not then return will show missing values
        if set(values.keys()) != set(['compOp', 'name', 'status', 'value']):
            return value
        # if status is set to skipped then the limit isn't validated
        if values['status'] == MeasureStatus.SKIPPED:
            return value
        # if compOp is LOG then the limit isn't validated and the limit should be None
        if values['compOp'] == StringCompOp.LOG:
            return value
        # for all other values of compOp the limit should be assigned
        if value is None:
            raise ValueError('EQ, NE, CASESENIT and IGNORECASE are single limit comparison operators; when used, '
                             'a limit value is required')
        return value

    @root_validator
    def validate_value_status(cls, svt_values):
        """
        This function will check that the set values match the status. If this is not the case then an error will be
        raised.

        For a status of skipped or a compOp of log there is no evaluation. All other states will be evaluated.

        :param svt_values:
        :return:
        """
        # print("validate_value_status", svt_values)
        # check if all the required values are assigned, if not then return will show missing values
        if missing := list(sorted(set(['compOp', 'status', 'value', 'limit']) - set(svt_values.keys()))):
            raise ValueError(f'Unable to evaluate string measure with failed fields: {missing}')
        # if status is skipped then the limit isn't validated
        if svt_values['status'] == MeasureStatus.SKIPPED:
            return svt_values
        # if compOp is LOG then the limit isn't validated and the limit should be None
        if svt_values['compOp'] == StringCompOp.LOG:
            return svt_values

        comp_dict = {StringCompOp.EQUAL: svt_values['value'] == svt_values['limit'],
                     StringCompOp.NI_EQUAL: svt_values['value'] == svt_values['limit'],
                     StringCompOp.NOT_EQUAL: svt_values['value'] != svt_values['limit'],
                     StringCompOp.CASE_SENSITIVE: svt_values['value'] == svt_values['limit'],
                     StringCompOp.CASE_IGNORE: svt_values['value'].upper() == svt_values['limit'].upper()}

        if svt_values['status'] != (MeasureStatus.FAILED, MeasureStatus.PASSED)[comp_dict[svt_values['compOp']]]:
            raise ValidationError([ErrorWrapper(ValueError('Evaluation of string value and limit does not match the '
                                                           'status'),
                                                loc=("status",))], model=cls)

        return svt_values


class StringValueEnhanced(StringValue):
    """
    The standard model will error if the status doesn't match the set values. The reason for this is to show if a
    report contains any errors so the user is able to identify issues with their program.

    When using the model to generate a report a benefit would be to allow the model to evaluate the status rather
    than setting the status in the model. This would negate the need for the user to write an evaluation in their
    code and this model will ensure that the value of the status is correct.
    """
    status: Literal[MeasureStatus.tuple()] = Field(None)

    @root_validator
    def validate_value_status(cls, svt_values):
        """
        This function overwrites the raise errors and now sets the status based on the values given.
        If the model is not given the values to evaluate the status it will raise an error.

        :param svt_values:
        :return:
        """
        # print("pre-validate_value_status", svt_values)
        # check if all the required values are assigned, if not then return will show missing values
        if set(svt_values.keys()) != set(['compOp', 'name', 'status', 'value', 'limit']):
            return svt_values
        # if status is skipped then the limit isn't validated
        if svt_values['status'] == MeasureStatus.SKIPPED:
            return svt_values
        # if compOp is LOG then the limit isn't validated and the limit should be None
        if svt_values['compOp'] == StringCompOp.LOG:
            svt_values['status'] = MeasureStatus.PASSED
            svt_values['limit'] = None
            return svt_values

        comp_dict = {StringCompOp.EQUAL: svt_values['value'] == svt_values['limit'],
                     StringCompOp.NI_EQUAL: svt_values['value'] == svt_values['limit'],
                     StringCompOp.NOT_EQUAL: svt_values['value'] != svt_values['limit'],
                     StringCompOp.CASE_SENSITIVE: svt_values['value'] == svt_values['limit'],
                     StringCompOp.CASE_IGNORE: svt_values['value'].upper() == svt_values['limit'].upper()}

        svt_values['status'] = (MeasureStatus.FAILED, MeasureStatus.PASSED)[comp_dict[svt_values['compOp']]]

        return svt_values


class NumericLimit(BaseModel):
    """
    Used to log numeric test data. the required fields are numericValue, units and CompOperator. Name must be present
    for multiple tests, but not for a single test.
    - numericMeas is a measurement, where the measurement is a number.

    Properties	    Data type	        Required
    compOp	        Enum (LOG, EQ, NE,  Yes
        LT, LE, GT, GE, LTGT, LTGE, LEGT,
        LEGE, GTLT, GTLE, GELT, GELE)
    highLimit	    Number	            If compOp is dual limit, yes
    highLimitFormat	String	            No
    lowLimit	    Number	            If compOp is single or dual   limit, yes
    lowLimitFormat	String	            No
    name	        String (100)	    If multiple numericMeas,   yes
    value	        Number	            Yes
    valueFormat	    String	            No
    status	        Character (P, F, S)	Yes
    unit	        String (20)	        Yes
    """
    compOp: Literal[NumericCompOp.tuple()] = Field(...)
    name: str = Field(None, min_length=1, max_length=100)
    status: Literal[MeasureStatus.tuple()] = Field(...)
    unit: str = Field(..., min_length=1, max_length=20)
    value: Decimal = Field(...)
    highLimit: Decimal = Field(None)
    lowLimit: Decimal = Field(None)

    @validator('highLimit', always=True)
    def validate_high_limit(cls, value, values):
        # print('highLimit', values)
        # check if all the required values are assigned, if not then return will show missing values
        if set(values.keys()) != set(['compOp', 'name', 'status', 'unit', 'value']):
            return value
        # if status is set to skipped then the limit isn't validated
        if values['status'] == MeasureStatus.SKIPPED:
            return value
        # if compOp is LOG then the limit isn't validated and the limit should be None
        if values['compOp'] == StringCompOp.LOG:
            return value
        # if compOp is single limit then highLimit should be None
        if values['compOp'] in ['EQ', 'NE', 'LT', 'LE', 'GT', 'GE']:
            if value is not None:
                raise ValueError('EQ, NE, LT, LE, GT, GE are all single limit comparison operators. When used, lowLimit'
                                 ' is required and highLimit is not supported')
            return value
        # for all other values of compOp the limit should be assigned
        if value is None:
            raise ValueError('LTGT, LTGE, LEGT, LEGE, GTLT, GTLE, GELT, GELE are all dual limit comparison operators. '
                             'When used, lowLimit and highLimit are both required. lowLimit and highLimit are '
                             'misnamed, think of them as limit1 and limit2 respectively')
        return value

    @validator('lowLimit', always=True)
    def validate_low_limit(cls, value, values):
        # print('lowLimit', values)
        # check if all the required values are assigned, if not then return will show missing values
        if set(values.keys()) != set(['compOp', 'name', 'status', 'unit', 'value', 'highLimit']):
            return value
        # if status is set to skipped then the limit isn't validated
        if values['status'] == MeasureStatus.SKIPPED:
            return value
        # if compOp is LOG then the limit isn't validated and the limit should be None
        if values['compOp'] == StringCompOp.LOG:
            return value
        # if compOp is single limit then lowLimit should be assigned
        if values['compOp'] in ['EQ', 'NE', 'LT', 'LE', 'GT', 'GE']:
            if value is None:
                raise ValueError(
                    'EQ, NE, LT, LE, GT, GE are all single limit comparison operators. When used, lowLimit'
                    ' is required and highLimit is not supported')
            return value
        # for all other values of compOp the limit should be assigned
        if value is None:
            raise ValueError(
                'LTGT, LTGE, LEGT, LEGE, GTLT, GTLE, GELT, GELE are all dual limit comparison operators. '
                'When used, lowLimit and highLimit are both required. lowLimit and highLimit are '
                'misnamed, think of them as limit1 and limit2 respectively')
        return value

    @root_validator
    def validate_status_value(cls, nvt_values):
        # nvt_values2 = SimpleNamespace(**{key: nvt_values.get(key) for key in cls.__fields__.keys()})
        # print(nvt_values2)
        # print('validate_status_value', nvt_values)
        # check if all the required values are assigned, if not then return will show missing values
        if missing := list(sorted(set(['compOp', 'status', 'value', 'highLimit', 'lowLimit']) - set(nvt_values.keys()))):
            raise ValueError(f'Unable to evaluate numeric measure with failed fields: {missing}')

        # if status is skipped then the limit isn't validated
        if nvt_values['status'] == MeasureStatus.SKIPPED:
            return nvt_values
        # if compOp is LOG then the limit isn't validated and the limit should be None
        if nvt_values['compOp'] == StringCompOp.LOG:
            return nvt_values

        single_comp_dict = {NumericCompOp.EQUAL: nvt_values['value'] == nvt_values['lowLimit'],
                            NumericCompOp.NI_EQUAL: nvt_values['value'] == nvt_values['lowLimit'],
                            NumericCompOp.NOT_EQUAL: nvt_values['value'] != nvt_values['lowLimit'],
                            NumericCompOp.LESS_THAN: nvt_values['value'] < nvt_values['lowLimit'],
                            NumericCompOp.LESS_OR_EQUAL: nvt_values['value'] <= nvt_values['lowLimit'],
                            NumericCompOp.GREATER_THAN: nvt_values['value'] > nvt_values['lowLimit'],
                            NumericCompOp.GREATER_OR_EQUAL: nvt_values['value'] >= nvt_values['lowLimit']}

        if nvt_values['compOp'] in single_comp_dict.keys():
            if nvt_values['status'] != (MeasureStatus.FAILED,
                                        MeasureStatus.PASSED)[single_comp_dict[nvt_values['compOp']]]:
                raise ValidationError(
                    [ErrorWrapper(ValueError('Evaluation of numeric value and low limit does not match the status'),
                                  loc=("status",)),
                     ErrorWrapper(ValueError('Evaluation of numeric value and low limit does not match the status'),
                                  loc=("value",)),
                     ErrorWrapper(ValueError('Evaluation of numeric value and low limit does not match the status'),
                                  loc=("lowLimit",))
                     ], model=cls)
            return nvt_values

        dual_comp_dict = {
            NumericCompOp.LESS_LOWER_GREATER_HIGHER:
                nvt_values['lowLimit'] > nvt_values['value'] > nvt_values['highLimit'],
            NumericCompOp.LESS_LOWER_GREATER_EQUAL:
                nvt_values['lowLimit'] > nvt_values['value'] >= nvt_values['highLimit'],
            NumericCompOp.LESS_EQUAL_GREATER_HIGHER:
                nvt_values['lowLimit'] >= nvt_values['value'] > nvt_values['highLimit'],
            NumericCompOp.LESS_EQUAL_GREATER_EQUAL:
                nvt_values['lowLimit'] >= nvt_values['value'] >= nvt_values['highLimit'],
            NumericCompOp.GREATER_LOWER_LESS_HIGHER:
                nvt_values['lowLimit'] < nvt_values['value'] < nvt_values['highLimit'],
            NumericCompOp.GREATER_LOWER_LESS_EQUAL:
                nvt_values['lowLimit'] < nvt_values['value'] <= nvt_values['highLimit'],
            NumericCompOp.GREATER_EQUAL_LESS_HIGHER:
                nvt_values['lowLimit'] <= nvt_values['value'] < nvt_values['highLimit'],
            NumericCompOp.GREATER_EQUAL_LESS_EQUAL:
                nvt_values['lowLimit'] <= nvt_values['value'] <= nvt_values['highLimit']
        }

        if nvt_values['compOp'] in dual_comp_dict.keys():
            if nvt_values['status'] != (MeasureStatus.FAILED,
                                        MeasureStatus.PASSED)[dual_comp_dict[nvt_values['compOp']]]:
                raise ValidationError(
                    [ErrorWrapper(ValueError('Evaluation of numeric value with low '
                                             'and high limit does not match the status'),
                                  loc=("status",))], model=cls)
            return nvt_values

        return nvt_values


class NumericLimitEnhanced(NumericLimit):
    """
    The standard model will error if the status doesn't match the set values. The reason for this is to show if a
    report contains any errors so the user is able to identify issues with their program.

    When using the model to generate a report a benefit would be to allow the model to evaluate the status rather
    than setting the status in the model. This would negate the need for the user to write an evaluation in their
    code and this model will ensure that the value of the status is correct.
    """
    status: Literal[MeasureStatus.tuple()] = Field(None)

    @root_validator
    def validate_status_value(cls, nvt_values):
        # print('validate_status_value', nvt_values)
        # check if all the required values are assigned, if not then return will show missing values
        if set(nvt_values.keys()) != set(['compOp', 'name', 'status', 'unit', 'value', 'highLimit', 'lowLimit']):
            return nvt_values

        # if status is skipped then the limit isn't validated
        if nvt_values['status'] == MeasureStatus.SKIPPED:
            return nvt_values
        # if compOp is LOG then the limit isn't validated and the limit should be None
        if nvt_values['compOp'] == StringCompOp.LOG:
            nvt_values['status'] = MeasureStatus.PASSED
            return nvt_values

        single_comp_dict = {NumericCompOp.EQUAL: nvt_values['value'] == nvt_values['lowLimit'],
                            NumericCompOp.NOT_EQUAL: nvt_values['value'] != nvt_values['lowLimit'],
                            NumericCompOp.LESS_THAN: nvt_values['value'] < nvt_values['lowLimit'],
                            NumericCompOp.LESS_OR_EQUAL: nvt_values['value'] <= nvt_values['lowLimit'],
                            NumericCompOp.GREATER_THAN: nvt_values['value'] > nvt_values['lowLimit'],
                            NumericCompOp.GREATER_OR_EQUAL: nvt_values['value'] >= nvt_values['lowLimit']}

        if nvt_values['compOp'] in single_comp_dict.keys():
            nvt_values['status'] = (MeasureStatus.FAILED,
                                    MeasureStatus.PASSED)[single_comp_dict[nvt_values['compOp']]]
            return nvt_values

        dual_comp_dict = {
            NumericCompOp.LESS_LOWER_GREATER_HIGHER:
                nvt_values['lowLimit'] > nvt_values['value'] > nvt_values['highLimit'],
            NumericCompOp.LESS_LOWER_GREATER_EQUAL:
                nvt_values['lowLimit'] > nvt_values['value'] >= nvt_values['highLimit'],
            NumericCompOp.LESS_EQUAL_GREATER_HIGHER:
                nvt_values['lowLimit'] >= nvt_values['value'] > nvt_values['highLimit'],
            NumericCompOp.LESS_EQUAL_GREATER_EQUAL:
                nvt_values['lowLimit'] >= nvt_values['value'] >= nvt_values['highLimit'],
            NumericCompOp.GREATER_LOWER_LESS_HIGHER:
                nvt_values['lowLimit'] < nvt_values['value'] < nvt_values['highLimit'],
            NumericCompOp.GREATER_LOWER_LESS_EQUAL:
                nvt_values['lowLimit'] < nvt_values['value'] <= nvt_values['highLimit'],
            NumericCompOp.GREATER_EQUAL_LESS_HIGHER:
                nvt_values['lowLimit'] <= nvt_values['value'] < nvt_values['highLimit'],
            NumericCompOp.GREATER_EQUAL_LESS_EQUAL:
                nvt_values['lowLimit'] <= nvt_values['value'] <= nvt_values['highLimit']
        }

        if nvt_values['compOp'] in dual_comp_dict.keys():
            nvt_values['status'] = (MeasureStatus.FAILED,
                                    MeasureStatus.PASSED)[dual_comp_dict[nvt_values['compOp']]]
            return nvt_values

        return nvt_values

# from typing import List
# from types import SimpleNamespace
#
# steps = {"numericMeas": [
#     {
#         "compOp": "GELE",
#         "name": None,
#         "status": "F",
#         "unit": "volt",
#         "value": 17.879107705605,
#         "highLimit": 16,
#         "lowLimit": 14
#     },
#     {
#         "compOp": None,
#         "name": None,
#         "status": "F",
#         "unit": "volt",
#         "value": 17.879107705605,
#         "highLimit": 16,
#         "lowLimit": 14
#     },
#     {
#         "compOp": "GELE",
#         "name": None,
#         "status": None,
#         "unit": "volt",
#         "value": 17.879107705605,
#         "highLimit": 16,
#         "lowLimit": 14
#     },
#     {
#         "compOp": "GELE",
#         "name": None,
#         "status": "F",
#         "unit": None,
#         "value": 17.879107705605,
#         "highLimit": 16,
#         "lowLimit": 14
#     },
#     {
#         "compOp": "GELE",
#         "name": None,
#         "status": "F",
#         "unit": "volt",
#         "value": None,
#         "highLimit": 16,
#         "lowLimit": 14
#     },
#     {
#         "compOp": "GELE",
#         "name": None,
#         "status": "F",
#         "unit": "volt",
#         "value": 17.879107705605,
#         "highLimit": None,
#         "lowLimit": 14
#     },
#     {
#         "compOp": "GELE",
#         "name": None,
#         "status": "F",
#         "unit": "volt",
#         "value": 17.879107705605,
#         "highLimit": 16,
#         "lowLimit": None
#     },
#     {
#         "name": None,
#         "status": "F",
#         "unit": "volt",
#         "value": 18.879107705605,
#         "highLimit": 16,
#         "lowLimit": 14
#     },
# ]
# }
#
#
# class NumericMeas(BaseModel):
#     numericMeas: List[NumericLimit] = Field(...)
#
#     @validator('numericMeas', each_item=True)
#     def validate_numMeas(cls, value):
#         print('numericMeas', value)
#         return value
#
#     @root_validator
#     def validate_root(cls, values):
#         print('root', values)
#         cls.validate_numMeas({'val': 'bob'})
#         return values
#
#
#
# try:
#     m = NumericMeas(**steps)
#     print(m.json(indent=2))
# except ValidationError as e:
#     for error in [SimpleNamespace(**error) for error in e.errors()]:
#         print(f"{error.type:<28} | {str(error.loc):<36} | {error.msg}")

# try:
#     m = NumericLimit(compOp=NumericCompOp.GREATER_EQUAL_LESS_EQUAL, value=5.08788365708408,
#                              lowLimit=4.85, highLimit=5, status="P")
#     print(m.json(indent=2))
# except ValidationError as e:
#     print(e.json())
#     print(e.errors())
