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
    import openpyxl as exc
    wb = exc.load_workbook(filename=path)
    if sheetName:
        sheet = wb[sheetName]
    else:
        sheet = wb.active
    idColumnIx = None
    dataColumnIx = None
    for col in range(1, sheet.max_column + 1):
        cell = sheet.cell(column=col, row=1)
        if cell and cell.value:
            v = cell.value.strip()
            if v == idColumn:
                if idColumnIx is not None:
                    raise ValueError(f'Duplicate idColumn {idColumn} at {path}')
                idColumnIx = col
            elif v == dataColumn:
                if dataColumnIx is not None:
                    raise ValueError(f'Duplicate dataColumn {dataColumn} at {path}')
                dataColumnIx = col
    if dataColumnIx is None:
        # Check whether the name of the dataColumn is split over two rows
        last = ''
        firstRow = []
        for col in range(1, sheet.max_column + 1):
            cell = sheet.cell(column=col, row=1)
            if cell and cell.value:
                v = cell.value.strip()
                last = v
            else:
                v = last
            firstRow.append(v)
        for col in range(1, sheet.max_column + 1):
            cell = sheet.cell(column=col, row=2)
            if cell and cell.value:
                v = str(cell.value).strip()
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
        cell = sheet.cell(column=idColumnIx, row=row)
        if cell and cell.value:
            v = cell.value.strip()
            if v in idValue:
                if rowIx is not None:
                    raise ValueError(f'Duplicate ID {idValue} in column {idColumn} at {path}')
                rowIx = row
    if rowIx is None:
        raise ValueError(f'No row found with value {idValue} in column {idColumn} at {path}')
    verbose(f'Storing {data} at column={dataColumnIx}, row={rowIx} in {path} (sheet: {sheetName})')
    sheet.cell(column=dataColumnIx, row=rowIx, value=data)
    saveExcelSpreadsheet(path, wb)
