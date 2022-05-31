import unittest
import spreadsheet
import shell
import openpyxl as exc
import uuid

def spreadsheetTest(action, check=None, path='test-data/bewertung.xlsx', sheetName=None):
    with shell.tempDir(delete=False, dir='.') as d:
        name = f'test_{uuid.uuid4()}.xlsx'
        p = shell.pjoin(d, name)
        shell.cp(path, p)
        x = action(p)
        if check:
            wb = exc.load_workbook(filename=p)
            if sheetName:
                sheet = wb[sheetName]
            else:
                sheet = wb.active
            check(sheet)
        return x

class SpreadsheetTest(unittest.TestCase):

    def getFirstData(self, kind):
        sheetName = 'Punkte Prog'
        x = spreadsheetTest(
            lambda p: spreadsheet.getFirstDataFromRow(p, sheetName, ['hello', 'Hello'],
                spreadsheetKind=kind),
            sheetName=sheetName
        )
        self.assertEqual(3, x)

    @unittest.skip("opens excel")
    def test_getFirstData(self):
        self.getFirstData('openpyxl')
        self.getFirstData('xlwings')

    def replaceData(self, kind):
        sheetName = 'Punkte Prog'
        spreadsheetTest(
            lambda p: spreadsheet.replaceData(p, 'ID', 'foo', 'newfoo', sheetName=sheetName,
                spreadsheetKind=kind),
            lambda sheet: self.assertEqual('newfoo', sheet['A4'].value),
            sheetName=sheetName
        )

    @unittest.skip("opens excel")
    def test_replaceData(self):
        self.replaceData('openpyxl')

    def enterData(self, kind):
        sheetName = 'Punkte Prog'
        spreadsheetTest(
            lambda p: spreadsheet.enterData(p, 'ID', 'foo', 'A2 a C', 42, sheetName=sheetName,
                spreadsheetKind=kind),
            lambda sheet: self.assertEqual(42, sheet['B4'].value),
            sheetName=sheetName
        )

    @unittest.skip("opens excel")
    def test_enterData(self):
        self.enterData('openpyxl')
