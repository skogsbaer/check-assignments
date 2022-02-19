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
    for d in dicts:
        if k in d:
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

class Keys:
    mainFile = 'main-file'
    testFiles = 'test-files'
    testFile = 'test-file'
    testFilter = 'test-filter'
    testFilters = 'test-filters'
    dirsAreUids = 'dirs-are-uids'
    testDir = 'test-dir'
    testDirs = 'test-dirs'

@dataclass
class Assignment:
    id: int
    points: int
    kind: str
    dicts: list[Dict]
    def __post_init__(self):
        if type(self.id) != int:
            raise TypeError("Assignment.id must be an int")
    def parse(id, dicts):
        points = getFromDicts(dicts, 'points', int)
        kind = getFromDicts(dicts, 'kind')
        return Assignment(id, points, kind, dicts)
    def getMainFile(self, d, fail=False):
        return self.getFile(Keys.mainFile, d, fail)
    def getGradleFile(self, d, fail=False):
        return self.getFile(Keys.gradleFile, d, fail)
    def getValue(self, k, fail=True):
        val = getFromDicts(self.dicts, k, fail=False)
        if val is None and fail:
            raise ValueError(f'Key {k} must be set for assignment {self.id}')
        else:
            return val
    def getFile(self, k, d, fail=True):
        x = getFromDicts(self.dicts, k, fail=fail)
        if x is not None:
            return shell.pjoin(d, x)
        else:
            if fail:
                raise ValueError(f'Key {k} must be set for assignment {self.id}')
            else:
                return None
    def getAsList(self, k):
        x = getFromDicts(self.dicts, k, default=[])
        if type(x) == list or type(x) == tuple:
            return x
        elif x:
            return [x]
        else:
            return []
    def getAsFileList(self, d, k):
        items = self.getAsList(k)
        return [shell.pjoin(d, x) for x in items]
    @property
    def copyItems(self):
        return self.getAsList('copy')

    def getTestDirs(self):
        return self._getTestSomething([Keys.testDir, Keys.testDirs])

    def getTestFilters(self):
        return self._getTestSomething([Keys.testFilter, Keys.testFilters])

    def getTestFiles(self, d):
        return self._getTestSomething([Keys.testFiles, Keys.testFile], lambda v: shell.pjoin(d, v))

    def _getTestSomething(self, keys, mapper=lambda x: x):
        result = []
        for x in [x for k in keys for x in self.getAsList(k)]:
            if isinstance(x, dict):
                for k, v in x.items():
                    testFile = mapper(v)
                    result.append( (k, testFile) )
            elif isinstance(x, str):
                try:
                    i = x.index(':')
                    k = x[:i]
                    v = mapper(x[i+1:])
                    result.append( (k, v) )
                except ValueError:
                    result.append( (x, mapper(x)) )
        return result

    @property
    def hasTests(self):
        disabled = getFromDicts(self.dicts, 'disable-tests', default=False)
        return not disabled
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
    def studentOutputFile(self, studentDir):
        return shell.pjoin(studentDir, f'OUTPUT_student_{self.id}.txt')
    def outputFile(self, studentDir, suffix=''):
        return shell.pjoin(studentDir, f'OUTPUT_{self.id}{suffix}.txt')
    @property
    def timeout(self):
        defTimeout = 10
        timeout = getFromDicts(self.dicts, 'timeout', default=defTimeout)
        if timeout == False:
            return None
        elif timeout == True:
            return defTimeout
        elif isinstance(timeout, int):
            return timeout
        else:
            raise Exception(f'Invalid type for timeout property of assignment {self.id}: ' \
                'must be a bool or an int')
    @property
    def scriptArgs(self):
        return self.getAsList("scriptArgs")

def expandVarsInStr(s, vars):
    return string.Template(s).safe_substitute(vars)

def expandVars(y, vars):
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
            result[k] = expandVars(v, vars)
        return result
    else:
        return y

uidRegex = re.compile('^[a-z0-9]+$')

@dataclass
class Config:
    baseDir: str
    assignments: List[Assignment]
    configDict: Dict
    testDir: str

    def __init__(self, baseDir, configDict, assignments, testDir):
        self.assignments = assignments
        self.configDict = configDict
        self.testDir = testDir
        self.baseDir = baseDir
        self.feedbackZip = 'feedback.zip'
        self.lang = 'de'

    @staticmethod
    def parse(baseDir, configDict, ymlDict):
        ymlDict.update(configDict)
        ymlDict = expandVars(ymlDict, ymlDict)
        assignments= []
        for k, v in ymlDict['assignments'].items():
            a = Assignment.parse(k, [v, ymlDict])
            assignments.append(a)
        testDir = ymlDict.get('test-dir', shell.pjoin(baseDir, 'tests'))
        return Config(baseDir, ymlDict, assignments, testDir)

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

    # A spreadsheet can be given as either
    # - FILEPATH (take the active sheet at FILEPATH)
    # - FILEPATH -> SHEET (take SHEET at FILEPATH)
    def getCustomRatingSheet(self):
        custom = self.configDict.get('rating-sheet', None)
        if custom:
            custom = custom.strip()
            l = custom.split('->')
            if len(l) <= 1:
                return (custom, None)
            elif len(l) == 2:
                return (l[0].strip(), l[1].strip())
            else:
                raise ValueError(f"Invalid sheet specification: {custom}")
        else:
            return None

    @property
    def spreadsheetPath(self):
        custom = self.getCustomRatingSheet()
        if custom:
            return custom[0]
        else:
            return shell.pjoin(self.baseDir, 'rating.xlsx')

    @property
    def spreadsheetAssignmentResultSheet(self):
        custom = self.getCustomRatingSheet()
        if custom:
            return custom[1]
        else:
            return None

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

def mkConfig(baseDir, configDict):
    if not shell.isdir(baseDir):
        abort('Base directory {baseDir} does not exist')
    yamlPath = shell.pjoin(baseDir, 'check.yml')
    if not shell.isFile(yamlPath):
        abort(f'Config file {yamlPath} not found')
    s = utils.readFile(yamlPath)
    ymlDict = yaml.load(s, Loader=yaml.FullLoader)
    cfg = Config.parse(baseDir, configDict, ymlDict)
    verbose(f"Parsed config: {cfg}")
    return cfg
