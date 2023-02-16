import utils
from config import *
import gradeCmd
from ansi import *
import spreadsheet
from dataclasses import dataclass

@dataclass
class CollectArgs:
    startAt: str
    targetFile: str
    sheetName: str

def collect(cfg: Config, args: CollectArgs):
    dirs = utils.collectSubmissionDirs(cfg, startAt=args.startAt)
    for studentDir in dirs:
        (name, id) = utils.parseSubmissionDir(cfg, studentDir)
        print(f'Collecting results for {name}')
        for a in cfg.assignments:
            print(f'    - Assignment {a.id}')
            (path, sheet) = gradeCmd.getSpreadsheet(studentDir, id, a, copy=False)
            if path is None:
                print(red(f"No spreadsheet found for {name}"))
            else:
                print(f'      Reading data from {path}')
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
                print(f'      Done reading data from {path}')
                targetFile = args.targetFile
                print(f'      Entering data into {targetFile}')
                spreadsheet.enterData(targetFile, ['Login', 'Matrikel'], id,
                    f"A{a.id}", p, args.sheetName)
                print(f'      Done entering data into {targetFile}')

