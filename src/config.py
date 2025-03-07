import shell
import os
from ownLogging import *
from dataclasses import dataclass
from typing import *
import yaml
import re
import utils
import string

def getFromDicts(dicts, k, conv=lambda x: x, default=None, fail=True):
    if type(dicts) is not list:
        dicts = [dicts]
    val = None
    for i, d in enumerate(dicts):
        if d is not None and k in d:
            val = d[k]
            break
    else:
        val = default
    if val is None:
        if fail:
            raise KeyError(f'Required key {k} not defined in {dicts[0]} and any of its parents')
        else:
            return None
    try:
        return conv(val)
    except:
        raise ValueError(f'Value for key {k} in {dicts[0]} has wrong type: {val}')

def getAsList(dicts, k):
    x = getFromDicts(dicts, k, default=[])
    if type(x) == list or type(x) == tuple:
        return x
    elif x:
        return [x]
    else:
        return []

class Keys:
    dirsAreUids = 'dirs-are-uids'
    tests = 'tests'
    points = 'points'
    kind = 'kind'
    mainFile = 'main-file'
    timeout = 'timeout'
    testDir = 'test-dir'
    testFile = 'test-file'
    testFiles = 'test-files'
    testFilter = 'test-filter'
    testFilters = 'test-filters'
    javaSimple = 'java-simple'

def defaultTestDir(baseDir):
    return shell.pjoin(baseDir, 'tests')

def defaultRatingSheet(baseDir):
    return shell.pjoin(baseDir, 'rating.xlsx')

@dataclass
class Test:
    id: str
    dir: str
    _filter: Optional[str]
    _file: Optional[str]

    @staticmethod
    def parse(baseDir, assignmentId: int, id: Optional[str], dicts: list[dict], fail: bool = True):
        dir = getFromDicts(dicts, 'test-dir', default=defaultTestDir(baseDir))
        file = getFromDicts(dicts, 'test-file', fail=False)
        if file:
            file = shell.pjoin(dir, file)
        filter = getFromDicts(dicts, 'test-filter', fail=False)
        testId = str(assignmentId)
        if id:
            testId = f'{testId}_{id}'
        if not file and not filter:
            if fail:
                testName = f'test "{id}"' if id else 'test'
                raise ValueError(f"Invalid {testName} without file and without filter")
            else:
                return None
        return Test(testId, dir, filter, file)

    def outputFile(self, studentDir):
        return shell.pjoin(studentDir, f'OUTPUT_{self.id}.txt')

    @property
    def file(self):
        x = self._file
        if x is None:
            raise ValueError(f'Test "{self.id}" has no file')
        return x

    @property
    def filter(self):
        x = self._filter
        if x is None:
            raise ValueError(f'Test "{self.id}" has no filter')
        return x

    @property
    def timeout(self):
        defTimeout = 10
        timeout = getFromDicts(self.dicts, Keys.timeout, default=defTimeout)
        if timeout == False:
            return None
        elif timeout == True:
            return defTimeout
        elif isinstance(timeout, int):
            return timeout
        else:
            raise Exception(f'Invalid type for timeout property of tests {self.id}: ' \
                'must be a bool or an int')
    @property
    def scriptArgs(self):
        return getAsList(self.dicts, "scriptArgs")

def getSingularPlural(dicts, kSing, kPlur):
    xs = getAsList(dicts, kSing)
    ys = getAsList(dicts, kPlur)
    return xs + ys

# A spreadsheet can be given as either
# - FILEPATH (take the active sheet at FILEPATH)
# - FILEPATH -> SHEET (take SHEET at FILEPATH)
def getCustomRatingSheet(dicts, key: str, kind: Literal['path', 'sheet'], assignmentId: Optional[int] = None):
    custom = getFromDicts(dicts, key, default=None, fail=False)
    if custom:
        if assignmentId:
            custom = expandAssignmentId(custom, assignmentId)
        custom = custom.strip()
        l = custom.split('->')
        if len(l) <= 1:
            path = custom
            sheet = None
        elif len(l) == 2:
            path = l[0].strip()
            sheet = l[1].strip()
        else:
            raise ValueError(f"Invalid sheet specification: {custom}")
    else:
        path = None
        sheet = None
    if kind == 'path':
        return path
    else:
        return sheet

def expandAssignmentId(x, id):
    return expandVars(x, {'N': str(id), 'NN': str(id).zfill(2)})

@dataclass
class Assignment:
    id: int
    baseDir: str
    points: int
    kind: str
    tests: list[Test]
    dicts: list[Dict]
    def __post_init__(self):
        if type(self.id) != int:
            raise TypeError("Assignment.id must be an int")
    @staticmethod
    def parse(baseDir, id, dicts):
        dicts = expandAssignmentId(dicts, id)
        points = getFromDicts(dicts, Keys.points, int)
        kind = getFromDicts(dicts, Keys.kind)
        tests = getFromDicts(dicts, Keys.tests, default={}, fail=False)
        if not tests:
            files = getSingularPlural(dicts, Keys.testFile, Keys.testFiles)
            filters = getSingularPlural(dicts, Keys.testFilter, Keys.testFilters)
            dir = getFromDicts(dicts, Keys.testDir, default=defaultTestDir(baseDir))
            parsedTests = []
            for f in files:
                testId = str(id)
                if len(files) + len(filters) > 1:
                    testId = f'{testId}_{shell.removeExt(shell.basename(f))}'
                parsedTests.append(Test(testId, dir, None, shell.pjoin(dir, f)))
            for f in filters:
                testId = str(id)
                if len(files) + len(filters) > 1:
                    testId = f'{testId}_{f.replace("*", "ALL")}'
                parsedTests.append(Test(testId, dir, f, None))
        else:
            parsedTests = []
            for k, v in tests.items():
                t = Test.parse(baseDir, id, k, [v] + dicts)
                parsedTests.append(t)
        disabledTests = getFromDicts(dicts, 'disable-tests', default=False)
        if disabledTests:
            parsedTests = []
        return Assignment(id, baseDir, points, kind, parsedTests, dicts)
    @property
    def itemsToCopy(self):
        return getAsList(self.dicts, 'copy')
    def studentOutputFile(self, studentDir):
        return shell.pjoin(studentDir, f'OUTPUT_{str(self.id)}_student.txt')
    def getMainFile(self, d, fail=False):
        return self._getFile(Keys.mainFile, d, fail)
    def dir(self, d):
        x = getFromDicts(self.dicts, 'dir', fail=False)
        if x is None:
            return None
        else:
            return shell.pjoin(d, x)
    def _getFile(self, k, d, fail=True):
        x = getFromDicts(self.dicts, k, fail=fail)
        if x is not None:
            return shell.pjoin(d, x)
        else:
            if fail:
                raise ValueError(f'Key {k} must be set for assignment {self.id}')
            else:
                return None
    @property
    def submissionFileGlob(self):
        return '*' + self.submissionFileExt
    @property
    def submissionFileExt(self):
        if self.kind == 'python':
            return '.py'
        elif self.kind == 'java':
            return '.java'
        elif self.kind == 'haskell':
            return '.hs'
        else:
            raise Exception(f"Unknown assignment kind: {self.kind}")

    @property
    def spreadsheetTemplatePath(self):
        return getCustomRatingSheet(self.dicts, 'rating-template', 'path')

    @property
    def spreadsheetTemplateAssignmentResultSheet(self):
        return getCustomRatingSheet(self.dicts, 'rating-template', 'sheet')

    @property
    def spreadsheetPath(self):
        p = getCustomRatingSheet(self.dicts, 'rating-sheet', 'path')
        if p is None:
            return defaultRatingSheet(self.baseDir)
        else:
            return p

    @property
    def spreadsheetAssignmentResultSheet(self):
        return getCustomRatingSheet(self.dicts, 'rating-sheet', 'sheet')

class MyTemplate(string.Template):
    braceidpattern = r'(?a:[_a-z][-_a-z0-9]*)'

def expandVarsInStr(s, vars):
    return MyTemplate(s).safe_substitute(vars)

def expandVars(y, vars):
    # print(f'expandVars({y}, {vars})')
    if isinstance(y, str):
        return expandVarsInStr(y, vars)
    elif isinstance(y, list):
        result = []
        for x in y:
            result.append(expandVars(x, vars))
        return result
    elif isinstance(y, dict):
        result = {}
        for k, v in y.items():
            newVars = vars.copy()
            newVars.update(result)
            result[k] = expandVars(v, newVars)
        return result
    else:
        return y

uidRegex = re.compile('^[a-z0-9A-Z]+$')

@dataclass
class Config:
    baseDir: str
    assignments: List[Assignment]
    configDict: Dict

    def __init__(self, baseDir, configDict, assignments):
        self.assignments = assignments
        self.configDict = configDict
        self.baseDir = baseDir
        self.feedbackZip = 'feedback.zip'
        self.lang = 'de'

    @staticmethod
    def parse(baseDir, configDict, ymlDict):
        ymlDict.update(configDict)
        ymlDict = expandVars(ymlDict, ymlDict)
        assignments= []
        if 'assignments' in ymlDict:
            for k, v in ymlDict['assignments'].items():
                a = Assignment.parse(baseDir, k, [v, ymlDict])
                assignments.append(a)
        return Config(baseDir, ymlDict, assignments)

    def isSubmissionDir(self, x):
        if self.configDict.get(Keys.dirsAreUids, False):
            return not not uidRegex.match(x)
        else:
            return x.endswith('_assignsubmission_file_')

    @property
    def gradlePath(self):
        return self.configDict.get('gradle', 'gradle')

    @property
    def wyppDir(self):
        return self.configDict.get('wypp', None)

    @property
    def ratingCsvPath(self):
        return shell.pjoin(self.baseDir, 'rating.csv')

    @property
    def editor(self):
        if os.environ.get('USER') == 'swehr':
            return 'edi' # special case
        else:
            return os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vim'

    @property
    def pointsTemplate(self):
        return shell.pjoin(self.baseDir, 'POINTS_template.txt')

    @property
    def pointsFile(self):
        return 'POINTS.txt'

    @property
    def commentsFile(self):
        return 'COMMENTS.txt'

    def _toplevelProp(self, k):
        x = self.configDict.get(k, None)
        if x is None:
            raise ValueError(f'No {k}  property at top-level')
        return x

    @property
    def testDir(self):
        return self._toplevelProp('test-dir')

    @property
    def kind(self):
        return self._toplevelProp('kind')

    @property
    def assignmentsGroupedByKind(self):
        d = {}
        for a in self.assignments:
            if a.kind in d:
                d[a.kind].append(a)
            else:
                d[a.kind] = [a]
        return d

    def studentCodedir(self, studentDir):
        sub = self.configDict.get('student-codedir', None)
        if sub:
            return shell.pjoin(studentDir, sub)
        else:
            return studentDir

    @property
    def spreadsheetPath(self):
        p = getCustomRatingSheet(self.configDict, 'rating-sheet', 'path')
        if p is None:
            return defaultRatingSheet(self.baseDir)
        else:
            return p

    def spreadsheetTemplatePath(self, assignmentId):
        return getCustomRatingSheet(self.configDict, 'rating-template', 'path', assignmentId)

    def spreadsheetTemplateAssignmentResultSheet(self, assignmentId):
        return getCustomRatingSheet(self.configDict, 'rating-template', 'sheet', assignmentId)

def mkConfig(baseDir, configDict):
    if not shell.isdir(baseDir):
        abort('Base directory {baseDir} does not exist')
    yamlPath = shell.pjoin(baseDir, 'check.yml')
    if not shell.isFile(yamlPath):
        abort(f'Config file {yamlPath} not found')
    s = utils.readFile(yamlPath)
    return mkConfigFromString(baseDir, configDict, s)

def mkConfigFromString(baseDir, configDict, s):
    ymlDict = yaml.load(s, Loader=yaml.FullLoader)
    cfg = Config.parse(baseDir, configDict, ymlDict)
    verbose(f"Parsed config: {cfg}")
    return cfg
