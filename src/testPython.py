from __future__ import annotations
from config import *
from ansi import *
from ownLogging import *
from testCommon import *
import sys

def runPythonTests(ctx, studentDir: str, assignment: Assignment):
    with shell.workingDir(studentDir):
        result = runTestScriptIfExisting(assignment, 'instructor', captureStdout=False,
                                        stderrToStdout=False)
    if result is None:
        tests = assignment.tests
        if tests:
            for t in tests:
                _runPythonTest(ctx, studentDir, assignment, t.id, testKindTutor,
                    mainFile=assignment.getMainFile(studentDir),
                    testFile=t.file,
                    logFile=t.outputFile(studentDir))
        else:
            _runPythonTest(ctx, studentDir, assignment, str(assignment.id), testKindStudent,
                mainFile=assignment.getMainFile(studentDir),
                testFile=None,
                logFile=assignment.studentOutputFile(studentDir))


def _runPythonTest(ctx, studentDir: str, assignment: Assignment, testId: str, testKind: TestKind,
                   mainFile: str, testFile: Optional[str], logFile: str):
    cfg = ctx.cfg
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
        args = ['--test-file', testFile, '--check', mainFile]
    else:
        args = ['--check', mainFile]
    runArgs = progArgs + args
    verbose(f'Running {runArgs}')
    with shell.createTee([shell.TEE_STDOUT, logFile]) as tee:
        result = shell.run(runArgs, onError='ignore', stderrToStdout=True, captureStdout=tee,
                           env={'PYTHONPATH': f'{wyppDir}/python/site-lib'})
    if result.exitcode == 0:
        print(green(f'Test {testId} OK'))
        spreadsheetResult = 1
    else:
        print(red(f'Test {testId} FAILED, see above'))
        spreadsheetResult = 0
    ctx.storeTestResultInSpreadsheet(studentDir, assignment, testId, [testKind], spreadsheetResult)
