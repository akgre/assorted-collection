from enum import Enum


class ExtendedEnum(str, Enum):
    """
    I recommend naming all enums UPPER_CASE. They're constants (within a namespace) and that's the rule for constants.

    You can only subclass a custom enumeration if it doesn’t have members.

    This class extends the functionality of the Enum class by adding two class methods, list and tuple, that allow
    for easy conversion of the Enum elements into either a list or a tuple.

    By adding the str class (known as mixin classes) this also means
    that class.member == class.member.value are the same.
    This makes it easier to use the enum member as the value and more like a class attribute.
    StrEnum is included in Python3.11
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def tuple(cls):
        return tuple(map(lambda c: c.value, cls))


class ReportType(ExtendedEnum):
    """
    Property: type
    Description: type of report
    Data Format: String(1)
    Importance: Required
    """
    TEST = 'T'
    REPAIR = 'R'


class StepGroup(ExtendedEnum):
    """
    Property: group
    Description: the step group
    Data Format: String(1)
    Importance: Required
    """
    SETUP = 'S'
    MAIN = 'M'
    CLEANUP = 'C'


class StepType(ExtendedEnum):
    """
    Property: group Description: The step type, a textual description of the step.
    Data Format: String(100)
    Importance: Required
    Comment: Step type doesn't get WATS to perform any behaviour and can technically be any
    string(100) outside the list below. They will tell WATS which icons to use in the report and the user can choose
    which ever is most useful to them.
    """
    SEQUENCE_CALL = 'SequenceCall'
    WATS_SEQUENCE_CALL = 'WATS_SeqCall'
    ACTION = 'Action'
    ET_ACTION = 'ET_A'
    LABEL = 'Label'
    CALL_EXE = 'CallExecutable'
    MESSAGE_POPUP = 'MessagePopup'
    PROPERTY_LOADER = 'PropertyLoader'
    GENERIC_STEP = 'GenericStep'
    ADDITIONAL_RESULTS = 'AdditionalResults'
    STATEMENT = 'Statement'
    NI_WAIT = 'NI_Wait'
    WAIT = 'Wait'
    CHART = 'WATS_XYGMNLT'
    ATTACHMENT = 'WATSFile'
    # attachment = 'WATS_AttachFile'
    SINGLE_PASS_FAIL = 'ET_PFT'
    MULTI_PASS_FAIL = 'ET_MPFT'
    SINGLE_STRING_VALUE = 'ET_SVT'
    MULTI_STRING_VALUE = 'ET_MSVT'
    SINGLE_NUMERIC_VALUE = 'ET_NLT'
    MULTI_NUMERIC_VALUE = 'ET_MNLT'
    XML_PT = "ET_XMLPT"


class MeasureStatus(ExtendedEnum):
    """
    For use in tests
    A single measurement (in a multiple step) can only be Passed or Failed or Skipped
    """
    PASSED = 'P'
    FAILED = 'F'
    SKIPPED = 'S'


class ResultStatus(ExtendedEnum):
    """
    Overall report result
    The UUT report itself can be Passed, Failed, Error or Terminated.
    """
    PASSED = 'P'
    FAILED = 'F'
    ERROR = 'E'
    TERMINATED = 'T'


class StepStatus(ExtendedEnum):
    """
    Step result
    A single step can have all statuses.
    """
    PASSED = 'P'
    FAILED = 'F'
    ERROR = 'E'
    TERMINATED = 'T'
    SKIPPED = 'S'
    DONE = 'D'
    UNKNOWN = 'U'


class StringCompOp(ExtendedEnum):
    LOG = 'LOG'
    NI_LOG = 'LOG DATA'
    EQUAL = 'EQ'
    NI_EQUAL = 'Equal'
    NOT_EQUAL = 'NE'
    CASE_SENSITIVE = 'CASESENSIT'
    CASE_IGNORE = 'IGNORECASE'


class NumericCompOp(ExtendedEnum):
    LOG = 'LOG'
    NI_LOG = 'LOG DATA'
    EQUAL = 'EQ'
    NI_EQUAL = 'Equal'
    NOT_EQUAL = 'NE'
    LESS_THAN = 'LT'
    LESS_OR_EQUAL = 'LE'
    GREATER_THAN = 'GT'
    GREATER_OR_EQUAL = 'GE'
    LESS_LOWER_GREATER_HIGHER = 'LTGT'
    LESS_LOWER_GREATER_EQUAL = 'LTGE'
    LESS_EQUAL_GREATER_HIGHER = 'LEGT'
    LESS_EQUAL_GREATER_EQUAL = 'LEGE'
    GREATER_LOWER_LESS_HIGHER = 'GTLT'
    GREATER_LOWER_LESS_EQUAL = 'GTLE'
    GREATER_EQUAL_LESS_HIGHER = 'GELT'
    GREATER_EQUAL_LESS_EQUAL = 'GELE'


class ChartTypes(ExtendedEnum):
    LINE = 'Line'
    LOGX = 'LineLogX'
    LOGY = 'LineLogY'
    LOGXY = 'LineLogXY'


class AdditionalDataTypes(ExtendedEnum):
    NUM = 'Number'
    STR = 'String'
    BOOL = 'Bool'
    OBJ = 'Obj'
    ARRAY = 'Array'
