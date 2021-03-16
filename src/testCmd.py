import shell
from dataclasses import dataclass
from utils import *
from ownLogging import *
from typing import *
from ansi import *
import re
import os
import testHaskell
import testPython
import testJava

@dataclass
class TestArgs:
    dirs: List[str]
    assignments: List[str] # take all if empty
    interactive: bool
    startAt: str

INSPECT_COMMAND = 'inspect'
RERUN_COMMAND = 'rerun'
CONTINUE_COMMAND = 'continue'
HELP_COMMAND = 'help'

def readCommand(cfg, args, studentDir, assignment):
    f = assignment.getMainFile(studentDir)
    commands = [('h?', HELP_COMMAND, 'Print this help message'),
                ('i', INSPECT_COMMAND, f'Inspect file {f}')]
    commands.append( ('r', RERUN_COMMAND, f'Re-run tests') )
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

def inspectFile(cfg, args, studentDir, assignment):
    f = assignment.getMainFile(studentDir)
    editor = cfg.editor()
    os.system(f"{editor} '{f}'")

TEST_DICT = {
    'python': testPython.runPythonTests,
    'java': testJava.runJavaTests,
    'haskell': testHaskell.runHaskellTests
}

def runTestsForAssignment(cfg, args, studentDir, assignment):
    k = assignment.kind
    if k in TEST_DICT:
        fun = TEST_DICT[k]
        fun(cfg, args, studentDir, assignment)
    else:
        abort(f"Don't know how to run tests for assignment kind {k}")

def interactiveLoop(cfg, args, studentDir, a):
    runTestsForAssignment(cfg, args, studentDir, a)
    if args.interactive:
        while True:
            print()
            print(studentDir)
            cmd = readCommand(cfg, args, studentDir, a)
            if cmd == INSPECT_COMMAND:
                inspectFile(cfg, args, studentDir, a)
            elif cmd == RERUN_COMMAND:
                runTestsForAssignment(cfg, args, studentDir, a)
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
        for i, a in enumerate(assignments):
            interactiveLoop(cfg, args, d, a)
            if i > 0:
                print()
