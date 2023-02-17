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
    count = 0
    for d in dirs:
        realD = shell.realpath(d)
        if realD == tmpl:
            continue
        ecode = shell.run(['diff', '-r', tmpl, realD], captureStdout=True, onError='ignore').exitcode
        student = shell.basename(d)
        rec = mapping.get(student)
        if not rec:
            raise ValueError(f'Student {student} not found in {args.sheet}')
        content = rec[args.contentKey]
        if ecode == 0:
            # unchanged submission
            if content:
                raise ValueError(f'Submission unchanged for student {student}, but data exists in {args.sheet}')
            count = count + 1
            if args.dry:
                print(f'Would remove {student} if not in dry-run mode')
            else:
                print(f'Removing {student}')
                shell.rmdir(d, True)
        else:
            # changed submission
            if not content:
                raise ValueError(f'Submission changed for student {student}, but no data in {args.sheet}')
    if args.dry:
        print(f'Would have removed {count} directories')
    else:
        print(f'Removed {count} directories')

