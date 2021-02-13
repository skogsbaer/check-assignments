import shell
from dataclasses import dataclass
from utils import *
from ownLogging import *
from typing import *
from ansi import *
import re
import os

@dataclass
class TestArgs:
    filesOrDirs: List[str]
    onlySyntax: bool
    interactive: bool
    startAt: str
    command: str

haskellTestRe = re.compile(r'Cases: (\d+)  Tried: (\d+)  Errors: (\d+)  Failures: (\d+)')

def runHaskellTests(file, testFile):
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

def runTestWithCustomCmd(cmd, file, testFile):
    result = shell.run([cmd, file] + ([testFile] if testFile else []), onError='ignore')
    if result.exitcode == 0:
        print(green(f'Tests for {file} OK'))
    else:
        print(red(f'Tests for {file} FAILED, see above'))

def runPythonTests(file, testFile):
    if testFile:
        result = shell.run(['run-your-program', '--test-file', testFile, '--check', file], onError='ignore')
    else:
        result = shell.run(['run-your-program', '--check', file], onError='ignore')
    if result.exitcode == 0:
        print(green(f'Tests for {file} OK'))
    else:
        print(red(f'Tests for {file} FAILED, see above'))

def checkPythonSyntax(f):
    result = shell.run(['run-your-program', '--check-runnable', f], onError='ignore')
    if result.exitcode == 0:
        verbose(green(f'Good syntax of {f}'))
    else:
        print(red(f'BAD syntax of {f}\n'))

INSPECT_COMMAND = 'inspect'
INSPECT_STUDENT_COMMAND = 'inspect-student'
RERUN_COMMAND = 'rerun'
RERUN_STUDENT_COMMAND = 'rerun-student'
CONTINUE_COMMAND = 'continue'
HELP_COMMAND = 'help'

def readCommand(cfg, args, f):
    realFile = resolveFile(cfg, args, f)
    haveTutorFile = (realFile != f)
    commands = [('h?', HELP_COMMAND, 'Print this help message'),
                ('i', INSPECT_COMMAND, f'Inspect file {realFile}')]
    if haveTutorFile:
        commands.append( ('j', INSPECT_STUDENT_COMMAND, f'Inspect file {f}') )
    commands.append( ('r', RERUN_COMMAND, f'Re-run tests in {realFile}') )
    if haveTutorFile:
        commands.append( ('x', RERUN_STUDENT_COMMAND, f'Re-run tests in {f}') )
    commands.append( ('c', CONTINUE_COMMAND, f'Continue with next student') )
    def printHelp():
        for char, cmd, help in commands:
            print(f'  {char}: {help}')
    shortcutHelp = [x[0] for x in commands]
    while True:
        c = input(f'What to do next? {"/".join(shortcutHelp)} ')
        for chars, cmd, help in commands:
            if c in chars:
                if cmd == HELP_COMMAND:
                    printHelp()
                else:
                    return cmd
                break
        else:
            print(f'Unknown command {c}.')
            printHelp()

def resolveFile(cfg, args, f):
    d = shell.dirname(f)
    tutorFile = shell.pjoin(d, 'TUTOR', shell.basename(f))
    if shell.isFile(tutorFile):
        return tutorFile
    else:
        return f

def inspectFile(cfg, args, f, forceStudent=False):
    realFile = resolveFile(cfg, args, f)
    if forceStudent:
        realFile = f
    editor = cfg.editor()
    os.system(f"{editor} '{realFile}'")

def runTestsForFile(cfg, args, f, forceStudent=False):
    base = shell.basename(f)
    testFile = shell.pjoin(cfg.testDir, base)
    realFile = resolveFile(cfg, args, f)
    if forceStudent:
        realFile = f
    print(f'Running tests on {realFile}')
    if not shell.isfile(testFile):
        testFile = None
        print(f'No tests defined for {f}, running only the tests defined by the student')
    if args.command:
        runTestWithCustomCmd(args.command, realFile, testFile)
    elif cfg.fileExt == '.py':
        runPythonTests(realFile, testFile)
    elif cfg.fileExt == '.hs':
        runHaskellTests(realFile, testFile)
    else:
        abort(f"Don't know how to run tests for extension {cfg.fileExt}")

def interactiveLoop(cfg, args, f):
    runTestsForFile(cfg, args, f)
    if args.interactive:
        while True:
            student = shell.basename(shell.dirname(f))
            print()
            print(student)
            cmd = readCommand(cfg, args, f)
            if cmd == INSPECT_COMMAND:
                inspectFile(cfg, args, f)
            elif cmd == INSPECT_STUDENT_COMMAND:
                inspectFile(cfg, args, f, forceStudent=True)
            elif cmd == RERUN_COMMAND:
                runTestsForFile(cfg, args, f)
            elif cmd == RERUN_STUDENT_COMMAND:
                runTestsForFile(cfg, args, f, forceStudent=True)
            elif cmd == CONTINUE_COMMAND:
                return

def checkSyntax(cfg, f):
    if cfg.fileExt == '.py':
        checkPythonSyntax(f)
    else:
        abort(f"Don't know how to check syntax for extension {cfg.fileExt}")

def runTests(cfg, args):
    filesOrDirs = args.filesOrDirs
    if not filesOrDirs:
        filesOrDirs = collectSubmissionDirs(cfg)
    filesOrDirs = sorted(filesOrDirs)
    if args.startAt:
        l = filesOrDirs
        filesOrDirs = []
        for x in l:
            if shell.basename(x) >= args.startAt:
                filesOrDirs.append(x)
            else:
                print(f'Skipping {x} as requested')
    for fileOrDir in filesOrDirs:
        if shell.isfile(fileOrDir):
            interactiveLoop(cfg, args, fileOrDir)
        else:
            tutorDir = shell.pjoin(fileOrDir, 'TUTOR')
            if not shell.isDir(tutorDir):
                shell.mkdir(tutorDir)
            files = collectSubmissionFiles(cfg, fileOrDir)
            if not files:
                print(f'No submission files in {fileOrDir} for configuration {cfg}')
            for i, f in enumerate(files):
                if args.onlySyntax:
                    checkSyntax(cfg, f)
                else:
                    interactiveLoop(cfg, args, f)
                    if i > 0:
                        print()
