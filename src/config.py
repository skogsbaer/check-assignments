import shell
import os
from ownLogging import *
from dataclasses import dataclass
from typing import *
import yaml
import utils

def getFromDicts(dicts, k, conv=lambda x: x, default=None):
    if type(dicts) is not list:
        dicts = [dicts]
    for d in dicts:
        if k in d:
            val = d[k]
            break
    else:
        if default:
            val = default
    if val is None:
        raise KeyError(f'Required key {k} not defined in {dicts[0]} and any of its parents')
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
    keyValues: Dict
    def parse(id, dicts):
        points = getFromDicts(dicts, 'points', int)
        kind = getFromDicts(dicts, 'kind')
        return Assignment(id, points, kind, dicts[0])
    def getMainFile(self, d):
        k = 'main-file'
        if k in self.keyValues:
            return shell.pjoin(d, self.keyValues[k])
        else:
            return None
    def getAsList(self, k):
        if k in self.keyValues:
            x = self.keyValues[k]
            if type(x) == list or type(x) == tuple:
                return x
            else:
                return [x]
        else:
            return []
    def getAsFileList(self, d, k):
        items = self.getAsList(k)
        return [shell.pjoin(d, x) for x in items]

@dataclass
class Config:
    baseDir: str
    assignments: List[str]
    testDir: str
    fileExt: str

    def __init__(self, baseDir, assignments, testDir, fileExt):
        self.assignments = assignments
        self.testDir = testDir
        self.baseDir = baseDir
        self.submissionDirGlob = '*_assignsubmission_file_'
        self.submissionDirTextGlob = '*_assignsubmission_onlinetext_'
        self.fileExt = fileExt
        self.submissionFileGlob = '*' + (fileExt if fileExt else "")
        self.feedbackZip = 'feedback.zip'
        self.lang = 'de'

    def parse(baseDir, dict):
        assignments= []
        for k, v in dict['assignments'].items():
            a = Assignment.parse(k, [v, dict])
            assignments.append(a)
        testDir = dict.get('testDir', shell.pjoin(baseDir, 'tests'))
        return Config(baseDir, assignments, testDir, "FIXME")

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

def mkConfig(baseDir):
    if not shell.isdir(baseDir):
        abort('Base directory {baseDir} does not exist')
    yamlPath = shell.pjoin(baseDir, 'check.yml')
    if not shell.isFile(yamlPath):
        abort(f'Config file {yamlPath} not found')
    s = utils.readFile(yamlPath)
    dict = yaml.load(s, Loader=yaml.FullLoader)
    return Config.parse(baseDir, dict)
