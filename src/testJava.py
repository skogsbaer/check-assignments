from __future__ import annotations
import shell
from utils import *
from ansi import *
from ownLogging import *
from config import Config, Assignment
from dataclasses import dataclass
import re
from typing import *

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
    d = assignment.dir('.')
    if d:
        withLimitedDir(studentDir, [d],
            lambda d: _runJavaTests(ctx, studentDir, ctx.cfg.studentCodedir(d), assignment))
    else:
        codeDir = ctx.cfg.studentCodedir(studentDir)
        _runJavaTests(ctx, studentDir, codeDir, assignment)

def _runJavaTests(ctx, studentDir: str, codeDir: str, assignment: Assignment):
    _runJavaTest(ctx, studentDir, codeDir, assignment, str(assignment.id), "NOT_EXISTING_TEST_DIR",
        None, hasTests=False, isStudent=True)
    _runJavaTest(ctx, studentDir, codeDir, assignment, str(assignment.id), codeDir,
        None, hasTests=True, isStudent=True)
    for t in assignment.tests:
        _runJavaTest(ctx, studentDir, codeDir, assignment, t.id, t.dir, t.filter,
            hasTests=True, isStudent=False)

def _runJavaTest(ctx, studentDir: str, codeDir: str, assignment: Assignment, testId: str, testDir: str,
    filter: Optional[str], hasTests: bool, isStudent: bool):
    cfg = ctx.cfg
    if filter is None:
        filter = '*'
    gradleProps = {
        'testFilter': filter,
        'testDir': testDir,
        'studentDir': codeDir
    }
    gradlePropArgs = []
    for k, v in gradleProps.items():
        gradlePropArgs.append(f'-P{k}={v}')
    print()
    what = ''
    if hasTests:
        if isStudent:
            what = 'student test'
        else:
            what = 'tutor test'
    else:
        if isStudent:
            what = 'student build'
        else:
            what = 'tutor build'
    print(blue(f"Starting {what} {testId}"))
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
        with shell.createTee([shell.TEE_STDOUT, logFileName]) as tee:
            result = shell.run(cmd, onError='ignore', stderrToStdout=True, captureStdout=tee)
        output = open(logFileName, 'r').read()
    if result.exitcode == 0:
        print(green(f'{firstUpper(what)} {testId} OK'))
    else:
        print(red(f'{firstUpper(what)} {testId} FAILED, see above'))
    result = Result.parseResult(output)
    prefix = 'S' if isStudent else ''
    ctx.storeTestResultInSpreadsheet(studentDir, assignment, testId, [prefix + 'C'],
        0 if result.compileError else 1)
    if hasTests:
        ctx.storeTestResultInSpreadsheet(studentDir, assignment, testId, [prefix + 'T'], result.ratio())
