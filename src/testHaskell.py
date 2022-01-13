from __future__ import annotations
import re
import shell
from ansi import *
from ownLogging import *
from config import Config, Assignment
import spreadsheet
import utils
from testCommon import *
from typing import *

moduleRe = re.compile(r'^module\s+([\w.]+)\s+where')
moduleReNoWhere = re.compile(r'^module\s+([\w.]+)')

def insertMainModule(lines):
    idx = 0
    for i, l in enumerate(lines):
        l = l.strip()
        if not (l == '' or l.startswith('{-')):
            idx = i
            break
    lines.insert(idx, 'module Main where')

def fixStudentCode(f):
    """
    Add "module Main where", remove old module line if existing.
    Returns the filename of the rewritten file (if necessary).
    """
    if not shell.isFile(f):
        return f
    newLines = []
    foundWeirdModLine = False
    foundModuleLine = False
    for l in open(f).readlines():
        m = moduleRe.match(l)
        if m:
            return f
        else:
            newLines.append(l.rstrip())
            if l.strip().startswith('module'):
                foundWeirdModLine = True
    if foundWeirdModLine and not foundModuleLine:
        print(f'Could not patch student file {f}: weird module line detected')
        return f
    insertMainModule(newLines)
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
    sanityCheck = ctx.args.sanityCheck
    if studMain not in ctx.acc:
        if sanityCheck:
            res = _typecheck(studMain, ['stack', 'exec', 'ghci', '--', studMain])
            ctx.failed = not res
        else:
            logFileStud = assignment.studentOuputFile(studentDir)
            result = _runHaskellTests(assignment.id,
                                      studentDir,
                                      studMain,
                                      withGhciOpts(['stack', 'ghci', studMain], ['-e', 'main']),
                                      logFileStud,
                                      'student')
            ctx.storeTestResultInSpreadsheet(studentDir, assignment, 'Stud Tests', result)
        ctx.acc = ctx.acc + [studMain]
    else:
        print(f"Students tests in {studMain} already run.")
    if sanityCheck:
        return
    testFiles = assignment.getTestFiles(ctx.cfg.testDir)
    results = {}
    for testFile in testFiles:
        print(f"Running tutor's tests in {testFile}")
        logFileTutor = shell.pjoin(studentDir, f'OUTPUT_{assignment.id}.txt')
        modName = findModuleName(testFile)
        if modName is None:
            print(red('No module name found in tutor test code. Cannot run tests!'))
        else:
            allOpts = withGhciOpts(['stack', 'ghci', studMain, testFile],
                                   ['-i' + ctx.cfg.testDir, '-e', f'{modName}.tutorMain'])
            result = _runHaskellTests(assignment.id, studentDir, studMain, allOpts, logFileTutor, 'instructor')
        results[testFile] = result
    if len(results) == 1:
        ctx.storeTestResultInSpreadsheet(studentDir, assignment, 'Tutor Tests', result)
    else:
        for testFile, result in results.items():
            ctx.storeTestResultInSpreadsheet(studentDir, assignment, 'Tutor Tests', result, testFile=testFile)
    if not testFiles:
        print("No tutor's tests defined")

haskellTestRe = re.compile(r'^Cases:\s*(\d+)\s*Tried:\s*(\d+)\s*Errors:\s*(\d+)\s*Failures:\s*(\d+)')

def ignoreLine(line):
    return line.startswith("Warning: Couldn't find a component for file target") or \
        line.strip() == 'Attempting to load the file anyway.' or \
        line.strip() == 'Configuring GHCi with the following packages:'

def massageTestOutput(out):
    out = out.replace('\r', '\n')
    res = []
    for line in out.split('\n'):
        line = line.rstrip()
        if not ignoreLine(line):
            res.append(line)
    return '\n'.join(res)

def _typecheck(file, cmdList):
    result = shell.run(cmdList, onError='ignore', input=':quit')
    if result.exitcode == 0:
        print(green(f'{file} compiled successfully'))
        return True
    else:
        print(red('f{file} has compile errors'))
        return False

def removeRedundantNewlines(lines):
    result = []
    lastWasNewline = False
    for l in lines:
        if not l:
            if not lastWasNewline:
                result.append('')
            lastWasNewline = True
        else:
            lastWasNewline = False
            result.append(l)
    return '\n'.join(result)

def _runHaskellTests(assignmentId, studentDir, file, cmdList, logFile, kind: Literal['student', 'instructor']):
    resultScript = runTestScriptIfExisting(assignmentId, studentDir, kind)
    if resultScript is None:
        result = shell.run(['timeout', '--signal', 'KILL', '10'] + cmdList, onError='ignore',
                           captureStdout=True, stderrToStdout=True)
    else:
        result = resultScript
    out = massageTestOutput(result.stdout)
    errMsg = None
    okMsg = None
    resultStr = None
    if result.exitcode in [0, 1]:
        logLines = ["Output of running instructor's tests",
                    "=====================================",
                    ""]
        lastCasesLine = None
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
                lastCasesLine = line
            else:
                logLines.append(line)
        logLines.append('')
        if lastCasesLine:
            logLines.append(lastCasesLine)
        utils.writeFile(logFile, removeRedundantNewlines(logLines))
        if cases is None:
            errMsg = f'No test output found for {file}'
            resultStr = 'no test output'
        elif failing:
            errMsg = f'{failing} failing tests for {file}'
            resultStr = round(1 - failing/cases, 2)
        elif cases == 0:
            errMsg = f'No tests defined in {file}'
            if kind == 'student':
                resultStr = 'no tests'
            else:
                resultStr = 1.0
        else:
            okMsg = f'Tests for {file} OK ({cases} test cases)'
            resultStr = 1.0
    elif result.exitcode in [124, -9]:
        errMsg = f'Test TIMEOUT'
        resultStr = 'timeout'
        utils.writeFile(logFile, out)
    else:
        errMsg = f'Tests for {file} FAILED with exit code {result.exitcode}, see above'
        resultStr = 'run failed'
        utils.writeFile(logFile, out)
    if errMsg:
        print(result.stdout)
        print(red(errMsg))
    elif okMsg:
        print(green(okMsg))
    else:
        abort('BUG: neiter errMsg nor okMsg was set')
    return resultStr
