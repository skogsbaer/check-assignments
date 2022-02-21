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

@dataclass
class GradeArgs:
    dirs: List[str]
    assignments: List[str] # take all if empty
    startAt: str

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

def copyTemplate(studentDir: str, studentId: str, path: str):
    (b, e) = shell.splitExt(shell.basename(path))
    for t in ['_TEMPLATE_', 'TEMPLATE_', '_TEMPLATE', 'TEMPLATE']:
        b = b.replace(t, '')
    b = b + '_' + studentId
    newPath = shell.pjoin(studentDir, b) + e
    if not shell.isFile(newPath):
        note(f"Copying template {path} to {newPath}")
        shell.cp(path, newPath)
        spreadsheet.replaceData(newPath, 'ID', 'STUDENT_ID', studentId)
    return newPath

def getSpreadsheet(studentDir: str, studentId: str, assignment: Assignment):
    templatePath = assignment.spreadsheetTemplatePath
    if templatePath:
        p = copyTemplate(studentDir, studentId, templatePath)
        return (p, assignment.spreadsheetTemplateAssignmentResultSheet)
    else:
        return (assignment.spreadsheetPath, assignment.spreadsheetAssignmentResultSheet)

def forEach(cfg: Config, args, action):
    dirs = args.dirs
    if not dirs:
        dirs = collectSubmissionDirs(cfg)
    dirs = sorted(dirs)
    verbose(f"Submission directories: {dirs}")
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
        action(d, assignments)
    return dirs


RERUN_COMMAND = 'rerun'
CONTINUE_COMMAND = 'continue'

def readCommand(cfg, args, mainFile):
    while True:
        try:
            c = input(f'What to do next? (ENTER to continue, r to grade the same student again) ')
        except EOFError:
            raise KeyboardInterrupt()
        if c == '':
            return CONTINUE_COMMAND
        elif c == 'r':
            return RERUN_COMMAND
        else:
            print("Invalid input")

def doGrade(cfg, args, studentDir, assignments):
    while True:
        (_name, id) = utils.parseSubmissionDir(cfg, studentDir)
        for a in assignments:
            print(blue(f'Grading assignment {a.id} of student {prettyStudent(cfg, studentDir)}'))
            (path, _sheet) = getSpreadsheet(studentDir, id, a)
            shell.run(['open', path])
            m = a.getMainFile(studentDir)
            shell.run([cfg.editor, m])
        print(blue(f'Just graded all assignments for student {prettyStudent(cfg, studentDir)}'))
        cmd = readCommand(cfg, args, None)
        if cmd == CONTINUE_COMMAND:
            return

def grade(cfg, args):
    def action(d, assignments):
        doGrade(cfg, args, d, assignments)
    forEach(cfg, args, action)
