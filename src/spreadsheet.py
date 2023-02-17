from typing import *
from ownLogging import *
from mySpreadsheet import *

def findColumnIndex(sheet: Sheet, title: Union[str, list[str]]) -> list[int]:
    if not isinstance(title, list):
        title = [title]
    ixs = []
    for col in sheet.colIndices():
        v = sheet.value(col=col, row=0)
        if v in title:
            ixs.append(col)
    return ixs

def findRowIndex(sheet, title: Union[str, list[str]]) -> Optional[int]:
    if not isinstance(title, list):
        title = [title]
    for row in sheet.rowIndices():
        v = sheet.value(col=0, row=row)
        if v in title:
            return row
    return None

SpreadsheetKind = Literal['openpyxl', 'xlwings']

def load(path, sheetName, k, dataOnly=False):
    if k == 'openpyxl':
        return XlsxSheet.load(path, sheetName, dataOnly=dataOnly)
    else:
        return XlwingsSheet.load(path, sheetName)

def getFirstDataFromRow(path: str, sheetName: str, rowTitle: Union[str, list[str]],
        spreadsheetKind: SpreadsheetKind = 'openpyxl'):
    with load(path, sheetName, spreadsheetKind, dataOnly=True) as sheet:
        row = findRowIndex(sheet, rowTitle)
        if row is None:
            raise ValueError(f"Sheet {sheetName} of spreadsheet {path} has no row with " \
                f"titles {rowTitle}")
        for col in sheet.colIndices(start=1):
            v = sheet.value(col=col, row=row)
            #print(f'row={row}, col={col}, v={v}')
            if v is not None:
                return v
        if spreadsheetKind == 'openpyxl':
            return getFirstDataFromRow(path, sheetName, rowTitle, 'xlwings')
        else:
            return None

def replaceData(path: str, colTitle: str, oldValue: str, newValue: str,
        sheetName: Optional[str] = None, spreadsheetKind: SpreadsheetKind = 'openpyxl'):
    with load(path, sheetName, spreadsheetKind) as sheet:
        idxs = findColumnIndex(sheet, colTitle)
        if not idxs:
            raise ValueError(f"No column found with title {colTitle}")
        if len(idxs) > 1:
            raise ValueError(f"More than one column found with title {colTitle}")
        idx = idxs[0]
        for row in range(0, sheet.numberOfRows):
            v = sheet.value(col=idx, row=row)
            if v:
                if v == oldValue:
                    sheet.setValue(col=idx, row=row, value=newValue)
        sheet.save(path)

def enterData(
    path: str,
    idColumn: str | list[str],
    idValue: Union[str, list[str]],
    dataColumn: str, data: str,
    sheetName: Optional[str] = None,
    spreadsheetKind: SpreadsheetKind = 'openpyxl'):
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
    with load(path, sheetName, spreadsheetKind) as sheet:
        idColumnIxs = findColumnIndex(sheet, idColumn)
        if not idColumnIxs:
            raise ValueError(f'No column named {idColumn} found at {path} ({sheetName})')
        dataColumnIxs = findColumnIndex(sheet, dataColumn)
        if not dataColumnIxs:
            # Check whether the name of the dataColumn is split over two rows
            last = ''
            firstRow = []
            for col in sheet.colIndices():
                v = sheet.value(col=col, row=0)
                if v:
                    v = str(v)
                    last = v
                else:
                    v = last
                firstRow.append(v)
            for col in sheet.colIndices():
                v = sheet.value(col=col, row=1)
                if v:
                    v = str(v)
                    if col - 1 < len(firstRow):
                        oneAbove = firstRow[col]
                        if (oneAbove + ' ' + v) == dataColumn or (oneAbove + v) == dataColumn:
                            if dataColumnIxs:
                                raise ValueError(f'Duplicate dataColumn {dataColumn} at {path}')
                            dataColumnIxs = [col]
        if not dataColumnIxs:
            dataColumnIx = sheet.numberOfCols
            sheet.setValue(col=dataColumnIx, row=0, value=dataColumn)
        else:
            dataColumnIx = dataColumnIxs[0]
        rowIx = None
        for row in sheet.rowIndices():
            for idColumnIx in idColumnIxs:
                v = sheet.value(col=idColumnIx, row=row)
                if v:
                    if v in idValue:
                        if rowIx is not None and rowIx != row:
                            raise ValueError(f'Duplicate ID {idValue} in column {idColumn} at {path}')
                        rowIx = row
        if rowIx is None:
            raise ValueError(f'No row found with value {idValue} in column {idColumn} at {path}')
        verbose(f'Storing {data} at col={dataColumnIx}, row={rowIx} in {path} (sheet: {sheetName})')
        sheet.setValue(col=dataColumnIx, row=rowIx, value=data)
        sheet.save(path)
        return f'{getColumnLetter(dataColumnIx)}{rowIx+1}'

