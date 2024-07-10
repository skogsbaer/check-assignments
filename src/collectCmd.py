import utils
from config import *
import gradeCmd
from ansi import *
import spreadsheet
from dataclasses import dataclass
from shell import *

@dataclass
class CollectArgs:
    startAt: str
    targetFile: str
    sheetName: str
    checkCompletenessOnly: bool
    eklausurenMoodle: bool

def repair(path):
    with spreadsheet.load(path, None, 'xlwings', dataOnly=False) as sheet:
        sheet.save(path)

def collect(cfg: Config, args: CollectArgs):
    dirs = utils.collectSubmissionDirs(cfg, startAt=args.startAt)
    errors = 0
    invalid = []
    for studentDir in dirs:
        (name, id) = utils.parseSubmissionDir(cfg, studentDir)
        print(f'Collecting results for {name}')
        for a in cfg.assignments:
            verbose(f'    - Assignment {a.id}')
            (path, sheet) = gradeCmd.getSpreadsheet(studentDir, id, a, copy=False)
            if path is None:
                print(red(f"No spreadsheet found for {name}"))
                errors += 1
            else:
                verbose(f'      Reading data from {path}')
                titles = [f'A{a.id} TOTAL', f'Aufgabe {a.id} TOTAL', 'Aufgabe TOTAL']
                p = spreadsheet.getFirstDataFromRow(path, sheet, titles)
                if p is None:
                    p = 0
                if p in [0, '0']:
                    done = spreadsheet.getFirstDataFromRow(path, sheet, ['Korrigiert?', 'korrigiert?'])
                    if done is not None and done.lower() in ['ja', 'yes', 'ok']:
                        pass
                    else:
                        print(red(f"No grading found in {path}"))
                if type(p) == str:
                    try:
                        float(p)
                    except ValueError:
                        print(red(f"Invalid grading found in {path}: Sometimes you have to reopen the file the force formula evaluation"))
                        errors += 1
                        invalid.append(path)
                if args.checkCompletenessOnly:
                    continue
                verbose(f'      Done reading data from {path}')
                targetFile = args.targetFile
                verbose(f'      Entering data into {targetFile}')
                lookupStudentId = id
                idCols = ['Login', 'Matrikel']
                if args.eklausurenMoodle:
                    lookupStudentId = fixEklausurenMoodleId(cfg, studentDir)
                    idCols = ['Name', 'Matrikel']
                    verbose(f'Using ID {lookupStudentId} for student {name} ({id})')
                spreadsheet.enterData(targetFile, idCols, lookupStudentId,
                    f"A{a.id}", p, args.sheetName)
                verbose(f'      Done entering data into {targetFile}')
    if errors:
        print(red(f'Found {errors} problems'))
    if invalid:
        print(red('The following files have invalid gradings:'))
        for x in invalid:
            print(x)
        print('Now trying to repair the files.')
        for x in invalid:
            repair(x)
        print('I tried to repair the files. Please run the completeness check again to see if this was successful.')
    elif args.checkCompletenessOnly:
        print('All grading complete (but not yet entered into the main spreadsheet)')

def fixEklausurenMoodleId(cfg, studentDir):
    """
    Eklausuren Moodle does not have Matriklernummers. So we have to turn the studentDir
    into Nachname,Vorname so that it can be found in the main spreadsheet.
    For very few students, this does not give a unique id. Hence, we also support a file
    studentDir/MATRIKEL.txt that may contain the matrikel number.
    """
    matrikelFile = pjoin(studentDir, 'MATRIKEL.txt')
    if isFile(matrikelFile):
        return readFile(matrikelFile).strip()
    x = utils.normalizeSubmissionDir(cfg, studentDir)
    try:
        i = x.index('_')
    except ValueError:
        raise ValueError('Invalid submission directory: ' + studentDir)
    name = x[:i]
    l = name.split(maxsplit=1)
    if len(l) == 1:
        return name
    else:
        first = l[0]
        last = l[1]
        return last + ',' + first
