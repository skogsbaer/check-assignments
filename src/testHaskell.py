from __future__ import annotations
import re
import shell
from ansi import *
from ownLogging import *
from config import Config, Assignment
import spreadsheet
import utils

moduleRe = re.compile(r'^module\s+([\w.]+)\s+where')
moduleReNoWhere = re.compile(r'^module\s+([\w.]+)')

def fixStudentCode(f):
    """
    Add "module Main where", remove old module line if existing.
    Returns the filename of the rewritten file (if necessary).
    """
    newLines = []
    foundWeirdModLine = False
    foundModuleLine = False
    for l in open(f).readlines():
        m = moduleRe.match(l)
        if m:
            foundModuleLine = True
            modName = m.group(1)
            if modName == 'Main':
                return f
            else:
                newLines.append('module Main where')
        else:
            newLines.append(l.rstrip())
            if l.strip().startswith('module'):
                foundWeirdModLine = True
    if foundWeirdModLine and not foundModuleLine:
        print(f'Could not patch student file {f}: weird module line detected')
        return f
    newLines.insert(0, 'module Main where')
    newName = shell.removeExt(f) + '_fixed.hs'
    open(newName, 'w').write('\n'.join(newLines))
    return newName

def findModuleName(f):
    """
    Extracts the module name from the given file.
    """
    for l in open(f).readlines():
        m = moduleRe.match(l)
        if m:
            modName = m.group(1)
            return modName
    return None

def withGhciOpts(opts, ghciOpts):
    res = opts[:]
    for x in ghciOpts:
        res.append('--ghci-options')
        res.append(x)
    return res

def runHaskellTests(ctx, studentDir: str, assignment: Assignment):
    if ctx.acc is None:
        ctx.acc = []
    studMain = fixStudentCode(assignment.getMainFile(studentDir))
    if studMain not in ctx.acc:
        logFileStud = shell.pjoin(studentDir, f'OUTPUT_student_{assignment.id}.txt')
        result = _runHaskellTests(studMain,
                                  withGhciOpts(['stack', 'ghci', studMain], ['-e', 'main']),
                                  logFileStud)
        ctx.storeTestResultInSpreadsheet(studentDir, assignment, 'Stud Tests', result)
        ctx.acc = ctx.acc + [studMain]
    else:
        print(f"Students tests in {studMain} already run.")
    testFiles = assignment.getTestFiles(ctx.cfg.testDir)
    for testFile in testFiles:
        print(f"Running tutor's tests in {testFile}")
        logFileTutor = shell.pjoin(studentDir, f'OUTPUT_tutor_{assignment.id}.txt')
        modName = findModuleName(testFile)
        if modName is None:
            print(red('No module name found in tutor test code. Cannot run tests!'))
        else:
            allOpts = withGhciOpts(['stack', 'ghci', studMain, testFile],
                                   ['-i' + ctx.cfg.testDir, '-e', f'{modName}.tutorMain'])
            result = _runHaskellTests(studMain, allOpts, logFileTutor)
            ctx.storeTestResultInSpreadsheet(studentDir, assignment, 'Tutor Tests', result)
    if not testFiles:
        print("No tutor's tests defined")

haskellTestRe = re.compile(r'^Cases:\s*(\d+)\s*Tried:\s*(\d+)\s*Errors:\s*(\d+)\s*Failures:\s*(\d+)')

def ignoreLine(line):
    return line.startswith("Warning: Couldn't find a component for file target") or \
        line.strip() == 'Attempting to load the file anyway.'

def messageTestOutput(out):
    out = out.replace('\r', '\n')
    res = []
    for line in out.split('\n'):
        line = line.rstrip()
        if not ignoreLine(line):
            res.append(line)
    return '\n'.join(res)

def _runHaskellTests(file, cmdList, logFile):
    result = shell.run(['timeout', '--signal', 'KILL', '10'] + cmdList, onError='ignore',
                       captureStdout=True, stderrToStdout=True)
    out = messageTestOutput(result.stdout)
    utils.writeFile(logFile, out)
    errMsg = None
    okMsg = None
    resultStr = None
    if result.exitcode in [0, 1]:
        cases = None
        failing = None
        for line in out.split('\n'):
            line = line.strip()
            m = haskellTestRe.match(line)
            if m:
                cases = int(m.group(1))
                errors = int(m.group(3))
                failures = int(m.group(4))
                failing = errors + failures
        if cases is None:
            errMsg = f'No test output found for {file}'
            resultStr = 'no test output'
        elif failing:
            errMsg = f'{failing} failing tests for {file}'
            resultStr = round(1 - failing/cases, 2)
        elif cases == 0:
            errMsg = f'No tests defined in {file}'
            resultStr = 'no tests'
        else:
            okMsg = f'Tests for {file} OK ({cases} test cases)'
            resultStr = 1.0
    elif result.exitcode in [124, -9]:
        errMsg = f'Test TIMEOUT'
        resultStr = 'timeout'
    else:
        errMsg = f'Tests for {file} FAILED with exit code {result.exitcode}, see above'
        resultStr = 'run failed'
    if errMsg:
        print(result.stdout)
        print(red(errMsg))
    elif okMsg:
        print(green(okMsg))
    else:
        abort('BUG: neiter errMsg nor okMsg was set')
    return resultStr
