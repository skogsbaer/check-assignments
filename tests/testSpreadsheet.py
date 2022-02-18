import unittest
import spreadsheet
import shell
import openpyxl as exc

class SpreadsheetTest(unittest.TestCase):
    def test_enterData(self):
        with shell.tempDir() as d:
            p = shell.pjoin(d, 'test.xlsx')
            shell.cp('test-data/bewertung.xlsx', p)
            sheetName = 'Punkte Prog'
            spreadsheet.enterData(p, 'ID', 'foo', 'A2 a C', 42, sheetName=sheetName)
            wb = exc.load_workbook(filename=p)
            if sheetName:
                sheet = wb[sheetName]
            else:
                sheet = wb.active
            self.assertEqual(42, sheet['B4'].value)
