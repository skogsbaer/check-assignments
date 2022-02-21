import os
import tempfile
from typing import *
from ownLogging import *

def saveExcelSpreadsheet(path: str, wb):
    # I experienced problem with corrupt .xlsx files, probably when the python process
    # was interrupted while writing the data.
    with tempfile.NamedTemporaryFile(suffix='.xlsx', dir=os.path.dirname(path)) as fp:
        fp.close()
        wb.save(fp.name)
        os.rename(fp.name, path) # Atomic move

def openSheet(path: str, sheetName: Optional[str]):
    import openpyxl as exc
    wb = exc.load_workbook(filename=path)
    if sheetName:
        sheet = wb[sheetName]
    else:
        sheet = wb.active
    return (wb, sheet)

def cellValue(sheet, column, row):
    cell = sheet.cell(column=column, row=row)
    if cell and cell.value:
        v = cell.value
        if isinstance(v, str):
            return v.strip()
        else:
            return v
    else:
        return None

def findColumnIndex(sheet, title: str) -> int:
    ix = None
    for col in range(1, sheet.max_column + 1):
        v = cellValue(sheet, column=col, row=1)
        if v:
            if v == title:
                if ix is not None:
                    raise ValueError(f'Duplicate column {title}')
                ix = col
    return ix

def replaceData(path: str, colTitle: str, oldValue: str, newValue: str,
    sheetName: Optional[str] = None):
    (wb, sheet) = openSheet(path, sheetName)
    idx = findColumnIndex(sheet, colTitle)
    for row in range(1, sheet.max_row + 1):
        v = cellValue(sheet, column=idx, row=row)
        if v:
            if v == oldValue:
                sheet.cell(column=idx, row=row, value=newValue)
    saveExcelSpreadsheet(path, wb)

def enterData(path: str,
    idColumn: str, idValue: Union[str, list[str]],
    dataColumn: str, data: str,
    sheetName: Optional[str] = None):
    """
    Enters some data into the spreadsheet stored at path.
    - idColumn is the name of the column containing IDs for the rows. This column must exist.
    - idValue is the value that is searched in idColum
    - dataColumn is the name of the column used for storing the data. This column may or may not exist.
      The name of the column might also be splitted in two rows
    - data is the data to be stored.
    """
    if not isinstance(idValue, list):
        idValue = [idValue]
    (wb, sheet) = openSheet(path, sheetName)
    idColumnIx = findColumnIndex(sheet, idColumn)
    dataColumnIx = findColumnIndex(sheet, dataColumn)
    if dataColumnIx is None:
        # Check whether the name of the dataColumn is split over two rows
        last = ''
        firstRow = []
        for col in range(1, sheet.max_column + 1):
            v = cellValue(sheet, column=col, row=1)
            if v:
                v = str(v)
                last = v
            else:
                v = last
            firstRow.append(v)
        for col in range(1, sheet.max_column + 1):
            v = cellValue(sheet, column=col, row=2)
            if v:
                v = str(v)
                if col - 1 < len(firstRow):
                    oneAbove = firstRow[col - 1]
                    if (oneAbove + ' ' + v) == dataColumn or (oneAbove + v) == dataColumn:
                        if dataColumnIx is not None:
                            raise ValueError(f'Duplicate dataColumn {dataColumn} at {path}')
                        dataColumnIx = col
    if idColumnIx is None:
        raise ValueError(f'No column named {idColumn} found at {path} ({sheetName})')
    if dataColumnIx is None:
        dataColumnIx = sheet.max_column + 1
        sheet.cell(column=dataColumnIx, row=1, value=dataColumn)
    rowIx = None
    for row in range(1, sheet.max_row + 1):
        v = cellValue(sheet, column=idColumnIx, row=row)
        if v:
            if v in idValue:
                if rowIx is not None:
                    raise ValueError(f'Duplicate ID {idValue} in column {idColumn} at {path}')
                rowIx = row
    if rowIx is None:
        raise ValueError(f'No row found with value {idValue} in column {idColumn} at {path}')
    verbose(f'Storing {data} at column={dataColumnIx}, row={rowIx} in {path} (sheet: {sheetName})')
    sheet.cell(column=dataColumnIx, row=rowIx, value=data)
    saveExcelSpreadsheet(path, wb)
