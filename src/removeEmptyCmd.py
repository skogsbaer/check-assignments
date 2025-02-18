from dataclasses import dataclass
from ownLogging import *
from config import Config
from typing import *
from utils import *
import shell
from mySpreadsheet import *

@dataclass
class RemoveEmptyArgs:
    sheet: str
    uidKey: str     # column title in sheet with the uid of the student
    contentKey: str # column title in sheet that is filled for non-empty students (usually the first exercise)
    templateDir: str
    dirs: Optional[list[str]]
    dry: bool

def removeEmpty(cfg: Config, args: RemoveEmptyArgs):
    mapping = sheetAsDict(XlsxSheet.load(args.sheet), args.uidKey)
    dirs = args.dirs
    if not dirs:
        dirs = collectSubmissionDirs(cfg)
    tmpl = shell.realpath(args.templateDir)
    tmpFilesAndDirs = []
    exts: set[str] = set()
    for x in shell.ls(tmpl, '*'):
        tmpFilesAndDirs.append(x)
        if shell.isFile(x):
            exts.add(shell.getExt(x))
    count = 0
    toRemove = []
    for d in dirs:
        realD = shell.realpath(d)
        if realD == tmpl:
            continue
        changes = False
        for x in tmpFilesAndDirs:
            realX = shell.pjoin(realD, shell.basename(x))
            if shell.isDir(x) == shell.isDir(realX):
                ecode = shell.run(['diff', '-r', x, realX], captureStdout=True, onError='ignore').exitcode
                if ecode != 0:
                    changes = True
            else:
                changes = True
        realFiles = []
        for e in exts:
            with shell.workingDir(realD):
                realFiles = realFiles + shell.run(['gfind', '-type', 'f', '-name', '*.'+e ], captureStdout=shell.splitLines, onError='ignore').stdout
        for f in realFiles:
            print(tmpl)
            print(f)
            if not shell.isFile(shell.pjoin(tmpl, f)):
                changes = True
        student = shell.basename(d)
        rec = mapping.get(student)
        if not rec:
            raise ValueError(f'Student {student} not found in {args.sheet}')
        content = rec[args.contentKey.lower()]
        if not changes:
            # unchanged submission
            if content:
                raise ValueError(f'Submission unchanged for student {student}, but data exists in {args.sheet}')
            count = count + 1
            if args.dry:
                print(f'Would remove {student} if not in dry-run mode')
                toRemove.append(student)
            else:
                print(f'Removing {student}')
                shell.rmdir(d, True)
        else:
            # changed submission
            if not content:
                print(f'Submission changed for student {student}, but no data in column {args.contentKey} of {args.sheet}.')
    if args.dry:
        print()
        print(f'Would have removed {count} directories: ')
    else:
        print()
        print(f'Removed {count} directories')
    for x in sorted(toRemove):
        print(x)

