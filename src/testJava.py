from __future__ import annotations
import shell
from utils import *
from ansi import *
from ownLogging import *
from config import Config, Assignment
from dataclasses import dataclass
import re

testPassRegex = re.compile('> .* PASSED')
testFailRegex = re.compile('> .* FAIL')

@dataclass
class Result:
    compileError: bool
    testsTotal: int
    testsFailed: int

    def ratio(self):
        if self.testsTotal == 0:
            return -1
        return float(self.testsTotal - self.testsFailed) / self.testsTotal

    @staticmethod
    def parseResult(s: str):
        compileError = (':compileTestJava FAILED') in s or (':compileJava FAILED' in s)
        nPass = len(testPassRegex.findall(s))
        nFail = len(testFailRegex.findall(s))
        return Result(compileError, nPass + nFail, nFail)

def runJavaTests(ctx, studentDir: str, assignment: Assignment):
    cfg = ctx.cfg
    allFilters = assignment.getTestFilters()
    if not allFilters:
        allFilters = [('', '*')]
    allTestDirs = assignment.getTestDirs()
    if not allTestDirs:
        allTestDirs = [('', cfg.testDir)]
    for testDirId, testDir in allTestDirs:
        for filterId, filter in allFilters:
            testId = str(assignment.id)
            parts = []
            if len(allTestDirs) > 1 and testDirId:
                testId = f'{testId}_{testDirId}'
                parts.append(testDirId)
            if len(allFilters) > 1 and filterId:
                testId = f'{testId}_{filterId.replace("*", "-")}'
                parts.append(filterId)
            result = _runJavaTest(ctx, testDir, studentDir, testId, filter, assignment.hasTests)
            part = ' '.join(parts)
            ctx.storeTestResultInSpreadsheet(studentDir, assignment, 'C',
                0 if result.compileError else 1, part=part)
            ctx.storeTestResultInSpreadsheet(studentDir, assignment, 'T', result.ratio(), part=part)


def _runJavaTest(ctx, testDir: str, studentDir: str, testId: str, filter: str, hasTests: bool):
    cfg = ctx.cfg
    gradleProps = {
        'testFilter': filter,
        'testDir': testDir,
        'studentDir': cfg.studentCodedir(studentDir)
    }
    gradlePropArgs = []
    for k, v in gradleProps.items():
        gradlePropArgs.append(f'-P{k}={v}')
    print()
    print(blue(f"Starting test {testId}"))
    with shell.workingDir(cfg.baseDir):
        if not shell.isFile('build.gradle'):
            abort(f'No build.gradle file in {cfg.baseDir}, aborting')
        if not hasTests:
            gradleCmd = 'compileJava'
        else:
            gradleCmd = 'test'
        cmd = [cfg.gradlePath] + gradlePropArgs + [gradleCmd, '--rerun-tasks']
        print(f'Executing {" ".join(cmd)}')
        logFileName = shell.pjoin(studentDir, f'OUTPUT_{testId}.txt')
        tee = shell.createTee([shell.TEE_STDOUT, logFileName])
        result = shell.run(cmd, onError='ignore', stderrToStdout=True, captureStdout=tee)
        output = open(logFileName, 'r').read()
    if result.exitcode == 0:
        print(green(f'Tests for {testId} OK'))
    else:
        print(red(f'Tests for {testId} FAILED, see above'))
    return Result.parseResult(output)
