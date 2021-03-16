from __future__ import annotations
from config import *
from ansi import *

def runPythonTests(cfg: Config, args: TestArgs, studentDir: str, assignment: Assignment):
    testFiles = assignment.getAsFileList(cfg.testDir, Keys.testFiles) + \
        assignment.getAsFileList(cfg.testDir, Keys.testFile)
    file = assignment.getMainFile(studentDir)
    if testFiles:
        # FIXME: support multiple test files
        result = shell.run(['run-your-program', '--test-file', testFiles[0], '--check', file], onError='ignore')
    else:
        result = shell.run(['run-your-program', '--check', file], onError='ignore')
    if result.exitcode == 0:
        print(green(f'Tests for {file} OK'))
    else:
        print(red(f'Tests for {file} FAILED, see above'))
