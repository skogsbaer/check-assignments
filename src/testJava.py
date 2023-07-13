from __future__ import annotations
import shell
from utils import *
from ansi import *
from ownLogging import *
from config import Config, Assignment
from dataclasses import dataclass
import re
from typing import *
import time

testPassRegex = re.compile('> .* PASSED')
testFailRegex = re.compile('> .* FAIL')

@dataclass
class Result:
    compileError: bool
    runError: bool
    testsTotal: int
    testsFailed: int
    output: str

    def ratio(self):
        if self.testsTotal == 0:
            return -1
        return float(self.testsTotal - self.testsFailed) / self.testsTotal

    @staticmethod
    def parseResult(s: str):
        compileError = (':compileTestJava FAILED') in s or (':compileJava FAILED' in s)
        runError = (':run FAILED') in s
        nPass = len(testPassRegex.findall(s))
        nFail = len(testFailRegex.findall(s))
        if ':test FAILED' in s:
            nFail = nFail - 1
        if ':test PASSED' in s:
            nPassed = nPassed - 1
        return Result(compileError, runError, nPass + nFail, nFail, s)

def runJavaTests(ctx, studentDir: str, assignment: Assignment):
    d = assignment.dir('.')
    if d:
        withLimitedDir(studentDir, [d],
            lambda d: _runJavaTests(ctx, studentDir, ctx.cfg.studentCodedir(d), assignment))
    else:
        codeDir = ctx.cfg.studentCodedir(studentDir)
        _runJavaTests(ctx, studentDir, codeDir, assignment)

_packageRe = re.compile(r'^package\s+([a-zA-Z_0-9.]+)')

def getClassFromFile(f):
    s = shell.readFile(f)
    clsName = shell.removeExt(shell.basename(f))
    for l in s.split('\n'):
        m = _packageRe.match(s)
        if m:
            pkg = m.group(1)
            return pkg + '.' + clsName
    return clsName

def hasUnitTests(d):
    javaFiles = shell.run(f'find {d} -name "*.java"', captureStdout=shell.splitLines).stdout
    for j in javaFiles:
        s = shell.readFile(j)
        if '@Test' in s:
            return True
    return False

def appendOutputToFile(path, timestamp, s):
    print(f'writing to {path}')
    start = '/* *** OUTPUT START ***'
    lines = []
    with open(path, 'r') as f:
        for line in f.readlines():
            if line.strip() == start:
                break
            lines.append(line)
    content = ''.join(lines)
    if content and content[-1] != '\n':
        content += '\n\n'
    content += f'{start}\n{timestamp}\n\n{s}\n*/\n'
    with open(path, 'w') as f:
        f.write(content)

def _runJavaTests(ctx, studentDir: str, codeDir: str, assignment: Assignment):
    logFileName = shell.pjoin(studentDir, f'OUTPUT_{assignment.id}.txt')
    timestamp = time.ctime()
    shell.writeFile(logFileName, f"RUN: {timestamp}\n\n")
    noMainClass = "NOT_EXISTING_CLASS"
    # compile code
    compileResult = _runJavaTest(ctx, studentDir, codeDir, assignment, logFileName,
        testId=str(assignment.id),
        testDir="NOT_EXISTING_TEST_DIR",
        testFilter=None, kind='compile', mainClass=noMainClass, isStudent=True)
    if compileResult.compileError:
        return
    m = assignment.getMainFile(codeDir)
    if m:
        mainClass = getClassFromFile(m)
        runResult = _runJavaTest(ctx, studentDir, codeDir, assignment, logFileName,
            testId=str(assignment.id),
            testDir="NOT_EXISTING_TEST_DIR",
            testFilter=None, kind='run', mainClass=mainClass, isStudent=True)
        appendOutputToFile(assignment.getMainFile(studentDir), timestamp, runResult.output)
    if hasUnitTests(codeDir):
        _runJavaTest(ctx, studentDir, codeDir, assignment, logFileName,
            testId=str(assignment.id),
            testDir=codeDir, testFilter=None, kind='test', mainClass=noMainClass, isStudent=True)
    for t in assignment.tests:
        _runJavaTest(ctx, studentDir, codeDir, assignment, logFileName,
            testId=t.id,
            testDir=t.dir, testFilter=t.filter, kind='test', mainClass=noMainClass, isStudent=False)

def _runJavaTest(ctx, studentDir: str, codeDir: str, assignment: Assignment, logFileName,
    testId: str, testDir: str,
    testFilter: Optional[str],
    mainClass: str,
    kind: Literal['compile', 'run', 'test'], isStudent: bool):
    cfg = ctx.cfg
    if testFilter is None:
        testFilter = '*'
    gradleProps = {
        'testFilter': testFilter,
        'testDir': testDir,
        'studentDir': codeDir,
        'mainClass': mainClass
    }
    gradlePropArgs = []
    for k, v in gradleProps.items():
        gradlePropArgs.append(f'-P{k}={v}')
    print()
    what = ''
    if kind == 'test':
        if isStudent:
            what = 'student test'
        else:
            what = 'tutor test'
    elif kind == 'run':
        what = 'run'
    else:
        if isStudent:
            what = 'student build'
        else:
            what = 'tutor build'
    print(blue(f"Starting {what} {testId}"))
    myLog = '/tmp/check-assignments-java.log'
    with shell.workingDir(cfg.baseDir):
        if not shell.isFile('build.gradle'):
            abort(f'No build.gradle file in {cfg.baseDir}, aborting')
        if kind == 'test':
            gradleCmd = 'test'
        elif kind == 'run':
            gradleCmd = 'run'
        else:
            gradleCmd = 'compileJava'
        cmd = [cfg.gradlePath] + gradlePropArgs + [gradleCmd, '--rerun-tasks']
        print(f'Executing {" ".join(cmd)}')
        with shell.createTee([shell.TEE_STDOUT, (logFileName, 'a'), myLog]) as tee:
            result = shell.run(cmd, onError='ignore', stderrToStdout=True, captureStdout=tee)
        output = open(myLog, 'r').read()
    if result.exitcode == 0:
        print(green(f'{firstUpper(what)} {testId} OK'))
    else:
        print(red(f'{firstUpper(what)} {testId} FAILED, see above'))
    result = Result.parseResult(output)
    prefix = 'S' if isStudent else ''
    ctx.storeTestResultInSpreadsheet(studentDir, assignment, testId, [prefix + 'C'],
        0 if result.compileError else 1)
    if kind == 'run':
        ctx.storeTestResultInSpreadsheet(studentDir, assignment, testId, [prefix + 'R'],
            0 if result.runError else 1)
    if kind == 'test':
        ctx.storeTestResultInSpreadsheet(studentDir, assignment, testId, [prefix + 'T'], result.ratio())
    return result
