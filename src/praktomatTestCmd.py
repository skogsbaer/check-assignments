import gradeCmd
from dataclasses import dataclass
import config
import shell
import pickle
from typing import *
import spreadsheet
import utils
from ownLogging import *

@dataclass
class PrTestArgs:
    dirs: list[str]
    startAt: str
    assignments: list[str]
    praktomatArgs: list[str]

def getSpreadsheet(cfg: config.Config, studentDir: str, studentId: str, assignmentId: str, copy=True):
    templatePath = cfg.spreadsheetTemplatePath(assignmentId)
    if templatePath:
        p = gradeCmd.copyTemplate(studentDir, studentId, templatePath, copy)
        return (p, cfg.spreadsheetTemplateAssignmentResultSheet(assignmentId))
    else:
        raise ValueError('No rating-template specified')

@dataclass
class PrResult:
    assignmentId: str
    compileStatus: Literal['OK', 'FAIL', 'OK_BUT_SOME_MISSING']
    error: bool
    totalTests: int
    testErrors: int
    testFailures: int

    @staticmethod
    def fromDict(assignmentId: str, d: dict):
        error = False
        totalTests = 0
        testErrors = 0
        testFailures = 0
        for t in d['tests']:
            if t['error']:
                error = True
            totalTests += t['totalTests']
            testErrors += t['testErrors']
            testFailures += t['testFailures']
        return PrResult(assignmentId, d['compileStatus'], error, totalTests, testErrors, testFailures)

    def storeInSpreadsheet(self, cfg: config.Config, studentDir: str):
        ratio = '-'
        if self.totalTests > 0:
            ok = self.totalTests - self.testFailures - self.testErrors
            ratio = f'{ok/self.totalTests:.1f}'
        results = [
            ('SC', 1 if self.compileStatus == 'OK' else 0), # student code compiles
            ('C', 0 if self.error else 1), # Tutor code compiles
            ('T', ratio) # Tutor tests
        ]
        if shell.basename(studentDir) == 'MUSTERMANN':
            print(f'Would store the following for {studentDir} and assignment {self.assignmentId}: {results}')
            return
        (name, id) = utils.parseSubmissionDir(cfg, studentDir)
        (path, sheet) = getSpreadsheet(cfg, studentDir, id, self.assignmentId)
        for k, v in results:
            resultColTitle = f'{self.assignmentId} {k}'
            try:
                cell = spreadsheet.enterData(path,
                                            'ID', [f"Teilnehmer/in{id}", id],
                                            resultColTitle, v,
                                            sheetName=sheet)
                print(f'Stored test result "{v}" for "{name}" ({id}) in column "{resultColTitle}" '
                      f'at {path}. Cell: {cell}')
            except ValueError as e:
                print(f"ERROR storing test result in spreadsheet: {e}")


PRAKTOMAT_CHECK = '/Users/swehr/devel/praktomat-checkers/multi-checker/script/check.py'

def runPraktomatTest(cfg: config.Config, d, assignmentIds, extraArgs: list[str]):
    with shell.tempDir() as tmp:
        resFile = shell.pjoin(tmp, "result")
        baseCmd = ['python3', PRAKTOMAT_CHECK,
            '--result-file', resFile,
            '--submission-dir', d,
            '--test-dir', cfg.testDir,
            cfg.kind,
            '--sheet', '.'] + extraArgs
        if cfg.kind == 'python':
            baseCmd.extend(['--wypp', cfg.wyppDir])
        for x in assignmentIds:
            cmd = baseCmd + ['--assignment', x]
            res = shell.run(cmd, onError='ignore', stderrToStdout=True, captureStdout=True)
            logFile = shell.pjoin(d, f'OUTPUT_{x}.txt')
            utils.writeFile(logFile, res.stdout)
            print(res.stdout)
            if not shell.isFile(resFile):
                utils.abort(f'Praktomat checker did not produce result file {resFile}. '
                            f'Command: {" ".join(cmd)}')
            with open(resFile, 'rb') as f:
                resDict = pickle.load(f)
            res = PrResult.fromDict(x, resDict)
            res.storeInSpreadsheet(cfg, d)

def runTests(cfg: config.Config, args: PrTestArgs):
    def action(d, _assignments, _total, _i):
        print('running for ' + d)
        runPraktomatTest(cfg, d, args.assignments, args.praktomatArgs)
    gradeCmd.forEach(cfg, args, action)

