import utils
from config import *
import gradeCmd
from ansi import *
import spreadsheet

def collect(cfg: Config, targetFile: str):
    for studentDir in utils.collectSubmissionDirs(cfg):
        (name, id) = utils.parseSubmissionDir(cfg, studentDir)
        for a in cfg.assignments:
            (path, sheet) = gradeCmd.getSpreadsheet(studentDir, id, a, copy=False)
            if path is None:
                print(red(f"No spreadsheet found for {name}"))
            else:
                titles = [f'A{a.id} TOTAL', f'Aufgabe {a.id} TOTAL']
                p = spreadsheet.getFirstDataFromRow(path, sheet, titles)
                if p is None:
                    p = 0
                if p in [0, '0']:
                    done = spreadsheet.getFirstDataFromRow(path, sheet, ['Korrigiert?', 'korrigiert?'])
                    if done is not None and done.lower() in ['ja', 'yes', 'ok']:
                        pass
                    else:
                        print(red(f"No grading found in {path}"))
                spreadsheet.enterData(targetFile, ['Login', 'Matrikel'], id,
                    f"A{a.id}", p, 'Ergebnis')
