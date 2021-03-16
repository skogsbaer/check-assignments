from __future__ import annotations
import re
import shell
from ansi import *
from ownLogging import *

haskellTestRe = re.compile(r'Cases: (\d+)  Tried: (\d+)  Errors: (\d+)  Failures: (\d+)')

def runHaskellTests(cfg: Config, args: TestArgs, studentDir: str, assignment: Assignment):
    print("Running student's tests")
    _runHaskellTests(file, ['stack', 'ghci', file, '--ghci-options', '-e', '--ghci-options', 'main'])
    if testFile:
        print("Running tutor's tests")
        _runHaskellTests(file, ['stack', 'ghci', file, testFile, '--ghci-options', '-e', '--ghci-options', 'tutorMain'])
    else:
        print("No tutor's tests defined")

def _runHaskellTests(file, cmdList):
    result = shell.run(cmdList, onError='ignore', captureStdout=True, stderrToStdout=True)
    errMsg = None
    okMsg = None
    if result.exitcode == 0:
        cases = None
        failing = None
        for line in result.stdout.split('\n'):
            m = haskellTestRe.match(line.strip())
            if m:
                cases = int(m.group(1))
                errors = int(m.group(3))
                failures = int(m.group(4))
                failing = errors + failures
                break
        if cases is None:
            errMsg = f'No test output found for {file}'
        elif failing:
            errMsg = f'{failing} failing tests for {file}'
        elif cases == 0:
            errMsg = f'No tests defined in {file}'
        else:
            okMsg = f'Tests for {file} OK ({cases} test cases)'
    else:
        errMsg = f'Tests for {file} FAILED, see above'
    if errMsg:
        print(result.stdout)
        print(red(errMsg))
    elif okMsg:
        print(green(okMsg))
    else:
        abort('BUG: neiter errMsg nor okMsg was set')
