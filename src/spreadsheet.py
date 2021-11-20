def enterData(path: str, idColumn: str, idValue: str, dataColumn: str, data: str):
    """
    Enters some data into the spreadsheet stored at path.
    - idColumn is the name of the column containing IDs for the rows. This column must exist.
    - idValue is the value that is searched in idColum
    - dataColumn is the name of the column used for storing the data. This column may or may not exist.
    - data is the data to be stored.
    """
    import openpyxl as exc
    wb = exc.load_workbook(filename=path)
    sheet = wb.active
    idColumnIx = None
    dataColumnIx = None
    for col in range(1, sheet.max_column + 1):
        cell = sheet.cell(column=col, row=1)
        if cell:
            v = cell.value.strip()
            if v == idColumn:
                if idColumnIx is not None:
                    raise ValueError(f'Duplicate idColumn {idColumn} at {path}')
                idColumnIx = col
            elif v == dataColumn:
                dataColumnIx = col
    if idColumnIx is None:
        raise ValueError(f'No column named {idColumn} found at {path}')
    if dataColumnIx is None:
        dataColumnIx = sheet.max_column + 1
        sheet.cell(column=dataColumnIx, row=1, value=dataColumn)
    rowIx = None
    for row in range(1, sheet.max_row + 1):
        cell = sheet.cell(column=idColumnIx, row=row)
        if cell:
            v = cell.value.strip()
            if v == idValue:
                if rowIx is not None:
                    raise ValueError(f'Duplicate ID {idValue} in column {idColumn} at {path}')
                rowIx = row
    if rowIx is None:
        raise ValueError(f'No row found with {idValue} in column {idColumn} at {path}')
    sheet.cell(column=dataColumnIx, row=rowIx, value=data)
    wb.save(path)
