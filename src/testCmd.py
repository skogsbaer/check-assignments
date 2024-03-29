import shell
from dataclasses import dataclass
from utils import *
from ownLogging import *
from typing import *
from ansi import *
import shell
import re
import os
from config import Config, Assignment
import testHaskell
import testPython
import testJava
import utils
import spreadsheet
from testCommon import *
from ownLogging import *
import gradeCmd

@dataclass
class TestArgs:
    dirs: List[str]
    assignments: List[str] # take all if empty
    interactive: bool
    startAt: str
    sanityCheck: bool
    openSpreadsheet: bool

class Context:
    def __init__(self, cfg: Config, args: TestArgs):
        self.cfg = cfg
        self.args = args
        self.acc = None
        self.failed = None # None means unknown, True definitive failure and False definitive success
    def storeTestResultInSpreadsheet(self, studentDir: str, assignment: Assignment,
            testId: str, suffixes: Union[str, list[str]], result: any):
        if type(suffixes) == str:
            suffixes = [suffixes]
        (name, id) = utils.parseSubmissionDir(self.cfg, studentDir)
        (path, sheet) = gradeCmd.getSpreadsheet(studentDir, id, assignment)
        if not shell.isFile(path):
            print(red(f'No spreadsheet at {path}, continuing without storing results'))
            return
        resultColTitle = testId
        if suffixes:
            resultColTitle = f'{resultColTitle} {" ".join(suffixes)}'
        try:
            cell = spreadsheet.enterData(path, 'ID', [f"Teilnehmer/in{id}", id], resultColTitle, result,
                sheetName=sheet)
            print(f'Stored test result "{result}" for "{name}" ({id}) in column "{resultColTitle}" at {path}. Cell: {cell}')
        except ValueError as e:
            print(f"ERROR storing test result in spreadsheet: {e}")

INSPECT_COMMAND = 'inspect'
RERUN_COMMAND = 'rerun'
CONTINUE_COMMAND = 'continue'
HELP_COMMAND = 'help'

def readCommand(cfg, args, mainFile):
    commands = [('h', HELP_COMMAND, 'Print this help message')]
    if mainFile:
        commands.append( ('i', INSPECT_COMMAND, f'Inspect file {mainFile}') )
    commands.append( ('r', RERUN_COMMAND, f'Re-run tests') )
    commands.append( ('c', CONTINUE_COMMAND, f'Continue with next assignment/student') )
    def printHelp():
        for char, cmd, help in commands:
            print(f'  {char}: {help}')
    shortcutHelp = [x[0] for x in commands]
    while True:
        try:
            c = input(f'What to do next? {"/".join(shortcutHelp)} ')
        except EOFError:
            raise KeyboardInterrupt()
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

def inspectFile(cfg, args, mainFile):
    editor = cfg.editor()
    os.system(f"{editor} '{mainFile}'")

TEST_DICT = {
    'python': testPython.runPythonTests,
    'java': testJava.runJavaTests,
    'haskell': testHaskell.runHaskellTests
}

prettyStudent = gradeCmd.prettyStudent

def moveToBackup(path):
    if not shell.exists(path):
        return
    for i in range(1000):
        backupName = shell.pjoin(shell.dirname(path), '.' + shell.basename(path) + ".bak")
        if i > 0:
            backupName = backupName + "." + str(i)
        if not shell.exists(backupName):
            shell.mv(path, backupName)
            return
    raise ValueError(f"too many backups for {path}")

def copyIntoStudentDir(assignment: Assignment, studentDir: str):
    for src in assignment.itemsToCopy:
        target = shell.pjoin(studentDir, shell.basename(src))
        if not fileSystemItemEquals(src, target):
            print(f'Copying {src} to {studentDir} ...')
            moveToBackup(target)
            shell.cp(src, studentDir)

def runTestsForAssignment(ctx, studentDir, assignment: Assignment):
    copyIntoStudentDir(assignment, studentDir)
    print(blue(f'Checking assignment {assignment.id} for student {prettyStudent(ctx.cfg, studentDir)}'))
    k = assignment.kind
    if k in TEST_DICT:
        fun = TEST_DICT[k]
        fun(ctx, studentDir, assignment)
    else:
        abort(f"Don't know how to run tests for assignment kind {k}")

def openSpreadsheet(cfg: Config, studentDir: str, assignment: Assignment):
    (_name, id) = utils.parseSubmissionDir(cfg, studentDir)
    (path, _sheet) = gradeCmd.getSpreadsheet(studentDir, id, assignment)
    shell.run(['open', path])
    print(f'Opened grading spreadsheet at {path}')

def interactiveLoopAssignment(ctx, studentDir, a):
    runTestsForAssignment(ctx, studentDir, a)
    if ctx.args.interactive == 'assignment':
        while True:
            print()
            if ctx.args.openSpreadsheet:
                openSpreadsheet(ctx.cfg, studentDir, a)
            print(blue(f'Just checked assignment {a.id} for student {prettyStudent(ctx.cfg, studentDir)}'))
            mainFile = a.getMainFile(studentDir)
            cmd = readCommand(ctx.cfg, ctx.args, mainFile)
            if cmd == INSPECT_COMMAND:
                inspectFile(ctx, mainFile)
            elif cmd == RERUN_COMMAND:
                runTestsForAssignment(ctx, studentDir, a)
            elif cmd == CONTINUE_COMMAND:
                return

def interactiveLoopStudent(cfg, args, studentDir, assignments):
    ctx = Context(cfg, args)
    def run():
        for i, a in enumerate(assignments):
            interactiveLoopAssignment(ctx, studentDir, a)
            if i > 0:
                print()
    run()
    if args.interactive == 'student':
        while True:
            print()
            print(blue(f'Just checked all assignments for student {prettyStudent(cfg, studentDir)}'))
            cmd = readCommand(cfg, args, None)
            if cmd == RERUN_COMMAND:
                run()
            elif cmd == CONTINUE_COMMAND:
                return
    return ctx.failed

def runTests(cfg, args):
    failures = []
    success = []
    def action(d, assignments, total, i):
        failed = interactiveLoopStudent(cfg, args, d, assignments)
        if failed is True:
            failures.append(d)
        elif failed is False:
            success.append(d)
    dirs = gradeCmd.forEach(cfg, args, action)
    if failures:
        print()
        print(red(f'The following students failed: '))
        for f in failures:
            print(f'  - {f}')
    else:
        if len(success) == len(dirs):
            print(green(f'Checks succeeded for all {len(success)} students'))
