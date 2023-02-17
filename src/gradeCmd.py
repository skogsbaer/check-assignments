import shell
from dataclasses import dataclass
from utils import *
from ownLogging import *
from typing import *
from ansi import *
import shell
from config import Config, Assignment
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

def copyTemplate(studentDir: str, studentId: str, path: str, copy: bool):
    (b, e) = shell.splitExt(shell.basename(path))
    for t in ['_TEMPLATE_', 'TEMPLATE_', '_TEMPLATE', 'TEMPLATE']:
        b = b.replace(t, '')
    b = b + '_' + studentId
    newPath = shell.pjoin(studentDir, b) + e
    if not shell.isFile(newPath):
        if copy:
            note(f"Copying template {path} to {newPath}")
            shell.cp(path, newPath)
            spreadsheet.replaceData(newPath, 'ID', 'STUDENT_ID', studentId)
        else:
            return None
    return newPath

def getSpreadsheet(studentDir: str, studentId: str, assignment: Assignment, copy=True):
    templatePath = assignment.spreadsheetTemplatePath
    if templatePath:
        p = copyTemplate(studentDir, studentId, templatePath, copy)
        return (p, assignment.spreadsheetTemplateAssignmentResultSheet)
    else:
        return (assignment.spreadsheetPath, assignment.spreadsheetAssignmentResultSheet)

def forEach(cfg: Config, args, action):
    dirs = args.dirs
    if not dirs:
        dirs = collectSubmissionDirs(cfg, startAt=args.startAt)
    total = len(dirs)
    for i, d in enumerate(dirs):
        assignments = cfg.assignments
        if args.assignments:
            assignments = []
            for a in cfg.assignments:
                if str(a.id) in args.assignments:
                    assignments.append(a)
        if not assignments:
            print(f'No assignments found or selected!')
        action(d, assignments, total, i)
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

def doGrade(cfg, args, studentDir, assignments, studTotal, studIdx):
    while True:
        (_name, id) = utils.parseSubmissionDir(cfg, studentDir)
        total = studTotal * len(assignments)
        for i, a in enumerate(assignments):
            thisIdx = studIdx * len(assignments) + i + 1
            print()
            print(blue(f'[{thisIdx}/{total}] Grading assignment {a.id} of student {prettyStudent(cfg, studentDir)}'))
            (path, _sheet) = getSpreadsheet(studentDir, id, a)
            shell.run(['open', path])
            m = a.getMainFile(studentDir)
            if m:
                cmdList = ['code', '--new-window', '--wait', '--goto', m, studentDir]
                shell.run(cmdList)
            else:
                print(f'No main file found for assignment {a.id}')
                cmdList = ['code', '--new-window', '--wait', studentDir]
                shell.run(cmdList)
        print(blue(f'Just graded all assignments for student {prettyStudent(cfg, studentDir)}'))
        cmd = readCommand(cfg, args, None)
        if cmd == CONTINUE_COMMAND:
            return

def grade(cfg, args):
    def action(d, assignments, total, i):
        doGrade(cfg, args, d, assignments, total, i)
    forEach(cfg, args, action)
