import shell
import os
from ownLogging import *
from dataclasses import dataclass
from typing import *

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
    def spreadsheetPath(self):
        return shell.pjoin(self.baseDir, 'rating.xlsx')
    def ratingCsvPath(self):
        return shell.pjoin(self.baseDir, 'rating.csv')
    def lineCommentStart(self):
        if self.fileExt == '.py':
            return '# '
        elif self.fileExt == '.hs':
            return '-- '
    def editor(self):
        if os.environ.get('USER') == 'swehr':
            return 'edi' # special case
        else:
            return os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vim'
    def pointsTemplate(self):
        return shell.pjoin(self.baseDir, 'POINTS_template.txt')

def getAssignments(testDir, fileExt=None):
    if fileExt is None:
        allFiles = [f for f in shell.ls(testDir, '*') if shell.isfile(f)]
        if not allFiles:
            abort(f'Could not infer assigments: no files in test directory {testDir}')
        e = shell.getExt(allFiles[0])
        if all([shell.getExt(f) == e for f in allFiles]):
            return ([shell.basename(f) for f in allFiles], e)
        else:
            abort(f'Could not infer extension of submission files: no explicit extension given and ' +
                  f'the files in test directory {testDir} have different extensions')
    else:
        files = [f for f in shell.ls(testDir, '*' + fileExt)]
        if not files:
            abort(f'Could not infer assigments: no files with extension {fileExt} in test directory {testDir}')
        return ([shell.basename(f) for f in files], fileExt)

def mkConfig(baseDir, fileExt=None, assignments=None, testDir=None):
    if not shell.isdir(baseDir):
        abort('Base directory {baseDir} does not exist')
    if testDir is None:
        defaultTestDir = shell.pjoin(baseDir, 'tests')
        if shell.isdir(defaultTestDir):
            verbose(f'Using default test directory {defaultTestDir}')
            testDir = defaultTestDir
        else:
            verbose(f'Default test directory {defaultTestDir} does not exist')
    if testDir is not None and not shell.isdir(testDir):
        abort('Test directory {testDir} does not exist')
    if assignments is None and testDir is not None:
        (assignments, fileExt) = getAssignments(testDir, fileExt)
        verbose(f'Inferred names of assignment files from {testDir} with extension {fileExt}: {str(assignments)}')
    if not assignments:
        warn('No assignments given and it was not possible to infer them.')
        assignments = []
    return Config(baseDir, assignments, testDir, fileExt)
