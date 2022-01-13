import unittest
from filenamesCmd import *
import shell
import config
import ownLogging

def mkConfig(baseDir):
    assignments = [
        config.Assignment(1, 1, 'python', {'main-file': '1.py'}),
        config.Assignment(2, 1, 'python', {'main-file': '2.py'}),
        config.Assignment(3, 1, 'java', {'main-file': '3.java'}),
        config.Assignment(4, 1, 'java', {'main-file': '4.java'}),
    ]
    return config.Config(baseDir, {}, assignments, 'tests')

student = 'Test_12345_assignsubmission_file_'

def runTest(files, fun):
    with shell.tempDir() as d:
        c = mkConfig(d)
        studDir = shell.pjoin(d, student)
        shell.mkdir(studDir)
        for f in files:
            shell.touch(shell.pjoin(studDir, f))
        fun(c)

def runCheckTest(self, files, expectedResult):
    def fun(c):
        res = checkFilenames(c)
        self.assertEqual(expectedResult, res)
    runTest(files, fun)

def runFixTest(self, files, expectedFiles):
    def fun(c):
        fixFilenames(c)
        studDir = shell.pjoin(c.baseDir, student)
        existingFiles = [shell.basename(p) for p in shell.ls(studDir)]
        self.assertEqual(sorted(expectedFiles), sorted(existingFiles))
    runTest(files, fun)

class FilenamesTest(unittest.TestCase):

    def test_check(self):
        runCheckTest(self, [], {'java': 'missing', 'python': 'missing'})
        runCheckTest(self, ['1.py', '4.java'], {'java': 'missing', 'python': 'missing'})
        runCheckTest(self, ['1.py', '2.py', '3.py', '4.java'],
                     {'java': 'missing', 'python': 'ok'})
        runCheckTest(self, ['1.py', '4.java', '5.java'], {'java': 'missing-but-extra', 'python': 'missing'})
        runCheckTest(self, ['1.py', '2.py', '4.java'],
                     {'java': 'missing', 'python': 'ok'})
        runCheckTest(self, ['1.py', '2.py', '3.java', '4.java'], {'java': 'ok', 'python': 'ok'})

    def test_fix(self):
        # ownLogging.enableVerboseLogging()
        runFixTest(self, ['aufgabe_01.py', '2.py', '3.java', 'foo.java'],
                         ['1.py', '2.py', '3.java', '4.java'])
        runFixTest(self, ['aufgabe_01.py', 'aufgabe_2.py', '3.java', 'foo.java', 'bar.java'],
                         ['1.py', '2.py', '3.java', 'foo.java', 'bar.java'])
