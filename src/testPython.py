from __future__ import annotations
from config import *
from ansi import *
from ownLogging import *
import sys

def runPythonTests(ctx, studentDir: str, assignment: Assignment):
    cfg = ctx.cfg
    testFiles = assignment.getTestFiles(cfg.testDir)
    if len(testFiles) > 1:
        abort(f'Python supports only one test case')
        return
    elif len(testFiles) == 1:
        testFile = testFiles[0]
    else:
        testFile = None
    file = assignment.getMainFile(studentDir, fail=True)
    wyppDir = cfg.wyppDir
    if not wyppDir:
        abort(f'Directory for write-your-python program must be set for python tests')
    if not shell.isDir(wyppDir):
        abort(f'Directory {wyppDir} does not exist.')
    progArgs = [
        sys.executable,
        shell.pjoin(wyppDir, 'python/src/runYourProgram.py')
    ]
    if testFile:
        args = ['--test-file', testFile, '--check', file]
    else:
        args = ['--check', file]
    logFileName = shell.pjoin(studentDir, f'OUTPUT_{assignment.id}.txt')
    tee = shell.createTee([shell.TEE_STDOUT, logFileName])
    runArgs = progArgs + args
    verbose(f'Running {runArgs}')
    result = shell.run(runArgs, onError='ignore', stderrToStdout=True, captureStdout=tee,
                       env={'PYTHONPATH': f'{wyppDir}/python/site-lib'})
    if result.exitcode == 0:
        print(green(f'Tests for {assignment.id} OK'))
    else:
        print(red(f'Tests for {assignment.id} FAILED, see above'))
