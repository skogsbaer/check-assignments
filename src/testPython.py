from __future__ import annotations
from config import *
from ansi import *

def runPythonTests(cfg: Config, args: TestArgs, studentDir: str, assignment: Assignment):
    testFiles = assignment.getTestFiles(cfg.testDir)
    file = assignment.getMainFile(studentDir, fail=True)
    if testFiles:
        # FIXME: support multiple test files
        result = shell.run(['run-your-program', '--test-file', testFiles[0], '--check', file], onError='ignore')
    else:
        result = shell.run(['run-your-program', '--check', file], onError='ignore')
    if result.exitcode == 0:
        print(green(f'Tests for {assignment.id} OK'))
    else:
        print(red(f'Tests for {assignment.id} FAILED, see above'))
