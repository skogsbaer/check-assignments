import shell
from dataclasses import dataclass
from utils import *
from ownLogging import *
from typing import *
from ansi import *
import re
import os
from config import Config, Assignment
import testHaskell
import testPython
import testJava
import utils
import spreadsheet
@dataclass
class TestArgs:
    dirs: List[str]
    assignments: List[str] # take all if empty
    interactive: bool
    startAt: str

class Context:
    def __init__(self, cfg: Config, args: TestArgs):
        self.cfg = cfg
        self.args = args
        self.acc = None
    def storeTestResultInSpreadsheet(self, studentDir: str, assignment: Assignment, colPrefix: str, result: str):
        (name, _) = utils.parseSubmissionDir(self.cfg, studentDir)
        title = f'{colPrefix} A{assignment.id}'
        try:
            path = self.cfg.spreadsheetPath
            spreadsheet.enterData(path, 'Vollständiger Name', name, title, result)
            print(f'Stored test result for {name} in {path}')
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

def prettyStudent(cfg, studentDir):
    try:
        (name, matrikel) = parseSubmissionDir(cfg, studentDir)
        return f'{name} ({matrikel})'
    except ValueError:
        x = shell.basename(studentDir)
        if not x:
            x = studentDir
        x = stripLeadingSlash(x)
        x = stripTrailingSlash(x)
        return x

def runTestsForAssignment(ctx, studentDir, assignment):
    print(blue(f'Checking assignment {assignment.id} for student {prettyStudent(ctx.cfg, studentDir)}'))
    k = assignment.kind
    if k in TEST_DICT:
        fun = TEST_DICT[k]
        fun(ctx, studentDir, assignment)
    else:
        abort(f"Don't know how to run tests for assignment kind {k}")

def interactiveLoopAssignment(ctx, studentDir, a):
    runTestsForAssignment(ctx, studentDir, a)
    if ctx.args.interactive == 'assignment':
        while True:
            print()
            print(blue(f'Just checked assignment {a.id} for student {prettyStudent(ctx.cfg, studentDir)}'))
            mainFile = a.getMainFile(studentDir)
            cmd = readCommand(ctx, mainFile)
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

def runTests(cfg, args):
    dirs = args.dirs
    if not dirs:
        dirs = collectSubmissionDirs(cfg)
    dirs = sorted(dirs)
    if args.startAt:
        l = dirs
        dirs = []
        for x in l:
            if shell.basename(x) >= args.startAt:
                dirs.append(x)
            else:
                print(f'Skipping {x} as requested')
    for d in dirs:
        assignments = cfg.assignments
        if args.assignments:
            assignments = []
            for a in cfg.assignments:
                if a.id in args.assignments:
                    assignments.append(a)
        if not assignments:
            print(f'No assignments found or selected!')
        interactiveLoopStudent(cfg, args, d, assignments)
