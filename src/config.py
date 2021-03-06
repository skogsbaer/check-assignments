import shell
import os
from ownLogging import *
from dataclasses import dataclass
from typing import *
import yaml
import utils

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

@dataclass
class Assignment:
    id: str
    points: int
    kind: str
    dicts: List[Dict]
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
    def getTestFiles(self, d):
        return self.getAsFileList(d, Keys.testFiles) + self.getAsFileList(d, Keys.testFile)
    @property
    def hasTests(self):
        disabled = getFromDicts(self.dicts, 'disable-tests', default=False)
        return not disabled

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
        self.submissionDirSuffix = '_assignsubmission_file_'
        self.submissionDirGlob = '*' + self.submissionDirSuffix
        self.submissionDirTextGlob = '*_assignsubmission_onlinetext_'
        self.feedbackZip = 'feedback.zip'
        self.lang = 'de'

    @staticmethod
    def parse(baseDir, configDict, ymlDict):
        assignments= []
        for k, v in ymlDict['assignments'].items():
            a = Assignment.parse(k, [v, ymlDict])
            assignments.append(a)
        testDir = ymlDict.get('test-dir', shell.pjoin(baseDir, 'tests'))
        return Config(baseDir, configDict, assignments, testDir)

    @property
    def gradlePath(self):
        return self.configDict.get('gradle', 'gradle')

    @property
    def wyppDir(self):
        return self.configDict.get('wypp', None)

    @property
    def spreadsheetPath(self):
        return shell.pjoin(self.baseDir, 'rating.xlsx')

    @property
    def ratingCsvPath(self):
        return shell.pjoin(self.baseDir, 'rating.csv')

    @property
    def lineCommentStart(self):
        if self.fileExt == '.py':
            return '# '
        elif self.fileExt == '.hs':
            return '-- '

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

def mkConfig(baseDir, configDict):
    if not shell.isdir(baseDir):
        abort('Base directory {baseDir} does not exist')
    yamlPath = shell.pjoin(baseDir, 'check.yml')
    if not shell.isFile(yamlPath):
        abort(f'Config file {yamlPath} not found')
    s = utils.readFile(yamlPath)
    ymlDict = yaml.load(s, Loader=yaml.FullLoader)
    return Config.parse(baseDir, configDict, ymlDict)
