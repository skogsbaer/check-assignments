from config import *
from ownLogging import *
from utils import *
from dataclasses import dataclass
import csv
from exportCmd import RATING_COL, NAME_COL, STATUS_COL
import string

@dataclass
class ImportArgs:
    csvFile: str

LETTERS = string.ascii_uppercase
MARK = '\ufeff'
FEEDBACK_COL = 'Feedback als Kommentar'

def sortKey(nameColIdx, names):
    def f(cols):
        name = cols[nameColIdx].strip()
        try:
            return names.index(name)
        except ValueError:
            return len(names)
    return f

def getNames(cfg):
    dirs = collectSubmissionDirs(cfg)
    names = []
    for d in dirs:
        try:
            (name, _) = parseSubmissionDir(cfg, d)
            names.append(name)
        except ValueError:
            pass
    return names

def importCmd(cfg, args):
    import openpyxl as exc
    assignments = []
    for i, a in enumerate(cfg.assignments):
        p = str(a.points)
        assignments.append(f'A{i+1} ({p})')
    with open(args.csvFile, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        csvRows = list(reader)
    if len(csvRows) == 0:
        abort(f'No rows in csv file {args.csvFile}')
    nameColIdx = -1
    ratingColIdx = -1
    statusColIdx = -1
    feedbackColIdx = -1
    for i, col in enumerate(csvRows[0]):
        if col == RATING_COL:
            ratingColIdx = i
        if col == NAME_COL:
            nameColIdx = i
        if col == STATUS_COL:
            statusColIdx = i
        if col == FEEDBACK_COL:
            feedbackColIdx = i
    if ratingColIdx < 0:
        abort(f'No column {RATING_COL} found in {args.csvFile}. Rows: {csvRows[0]}')
    if nameColIdx < 0:
        abort(f'No column {NAME_COL} found in {args.csvFile}. Rows: {csvRows[0]}')
    if feedbackColIdx < 0:
        abort(f'No column {FEEDBACK_COL} found in {args.csvFile}. Rows: {csvRows[0]}')
    contentCsvRows = csvRows[1:]
    names = getNames(cfg)
    if not names:
        abort('No submission directories found. Please provide them before running import or prepare')
    contentCsvRows.sort(key=sortKey(nameColIdx, names))
    sortedCsvRows = [csvRows[0]] + contentCsvRows
    filteredCsvRows = []
    for i, row in enumerate(sortedCsvRows):
        if row[statusColIdx].startswith('Keine Abgabe'):
            print(f'Keine Abgabe von {row[nameColIdx]}')
        else:
            filteredCsvRows.append(row)
    newRows = []
    for i, row in enumerate(filteredCsvRows):
        if i > 0:
            row[feedbackColIdx] = 'Siehe COMMENTS.txt und POINTS.txt'
        prefixCols = row[:ratingColIdx]
        if i == 0 and prefixCols[0].startswith(MARK):
            prefixCols[0] = prefixCols[0][len(MARK):]
        suffixCols = row[ratingColIdx+2:] if ratingColIdx < len(row) - 1 else []
        if i == 0:
            inbetweenCols = [RATING_COL] + assignments
        else:
            try:
                formulaStartCol = LETTERS[ratingColIdx + 1]
                formulaEndCol = LETTERS[ratingColIdx + 1 + len(assignments)]
            except IndexError:
                abort(f'Unexpected high number of cols in CSV file or unexpected high number of assignments. ')
            rowIdx = i + 1
            inbetweenCols = [f'=SUM({formulaStartCol}{rowIdx}:{formulaEndCol}{rowIdx})'] + (len(assignments) * [''])
        newRows.append(prefixCols + inbetweenCols + suffixCols)
    # Sort by lastname
    wb = exc.Workbook()
    ws = wb.active
    for r in newRows:
        ws.append(r)
    wb.save(cfg.spreadsheetPath)
