from __future__ import annotations
import shell
from utils import *
from ansi import *
from ownLogging import *
from config import Config, Assignment
import sys

x = ':compileTestJava FAILED'
y = '> test1() PASSED'
z = '> test3() FAILED'

def runJavaTests(ctx, studentDir: str, assignment: Assignment):
    cfg = ctx.cfg
    allFilters = assignment.getTestFilters()
    if not allFilters:
        allFilters = [('', '*')]
    for filterId, filter in allFilters:
        if len(allFilters) == 1 or not filterId:
            testId = str(assignment.id)
        else:
            testId = str(assignment.id) + '_' + filterId
        _runJavaTest(ctx, studentDir, testId, filter, assignment.hasTests)

def _runJavaTest(ctx, studentDir: str, testId: str, filter: str, hasTests: bool):
    cfg = ctx.cfg
    gradleProps = {
        'testFilter': filter,
        'testDir': cfg.testDir,
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
    if result.exitcode == 0:
        print(green(f'Tests for {testId} OK'))
    else:
        print(red(f'Tests for {testId} FAILED, see above'))
