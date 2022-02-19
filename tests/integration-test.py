#!/usr/bin/env python

import sys
import os
import zipfile
thisDir = os.path.dirname(__file__)
topDir = os.path.join(thisDir, '..')
sys.path.insert(0, os.path.join(topDir, 'src'))
import shell
import openpyxl as exc

checkAssignments = shell.abspath(shell.pjoin(topDir, 'check-assignments'))
if sys.platform == 'win32':
    checkAssignments = checkAssignments + ".bat"

def abort(msg):
    sys.stderr.write(msg + '\n')
    sys.exit(1)

def assertExists(path):
    if not shell.isFile(path):
        d = shell.dirname(path)
        files = shell.ls(d, '*')
        abort(f'File {path} does not exist, existing files: {files}')

def assertFileNotEmpty(path):
    assertExists(path)
    s = shell.readBinaryFile(path,)
    if not s:
        abort(f'File {path} is empty')

def assertEqual(expected, given):
    if expected != given:
        abort(f'Expected {expected}, given {given}')

with shell.tempDir(onException=False) as tmp:
    print(f'tmp={tmp}')
    shell.cp(shell.pjoin(topDir, 'test-data'), tmp)
    with shell.workingDir(shell.pjoin(tmp, 'test-data/submissions')):

        print('### import ###')
        shell.run([checkAssignments, 'import', '../rating-moodle.csv'])
        assertExists('rating.xlsx')

        print('### unzip ###')
        barFoo = 'Bar Foo_1234_assignsubmission_file_/'
        shell.run([checkAssignments, 'unzip'])
        assertExists(barFoo + 'assignment_01.py')

        print('### checkFilenames ###')
        shell.run([checkAssignments, 'checkFilenames'])
        shell.run([checkAssignments, 'fixFilenames'])

        print('### addComment ###')
        shell.run([checkAssignments, 'addComment'])
        assertExists(barFoo + 'COMMENTS.txt')

        print('### tests ###')
        shell.run([checkAssignments, 'runTests', '--interactive'], input='c\nc\nc\n')
        assertFileNotEmpty(shell.pjoin(barFoo, 'OUTPUT_1.txt'))
        assertFileNotEmpty(shell.pjoin(barFoo, 'OUTPUT_2.txt'))
        assertFileNotEmpty(shell.pjoin(barFoo, 'OUTPUT_3.txt'))
        assertFileNotEmpty(shell.pjoin(barFoo, 'OUTPUT_4.txt'))

        print()
        print('NOTE: the first test (python) should fail with "AssertionError: 41 != 42"')
        print('NOTE: the second test (java) should fail with "org.opentest4j.AssertionFailedError: expected: <1> but was: <0>"')
        print('NOTE: the third test (java) should work (no tests are run, only compiles)')
        print('NOTE: the fourth test (haskell) should fail with "expected 5 got 4"')

        # check contents of rating.xlsx
        ws = exc.load_workbook(filename = 'rating.xlsx').active
        rows = list(ws.rows)
        titleRow = [c.value for c in rows[0]]
        try:
            ix = titleRow.index('A1 TT')
        except ValueError:
            abort('Column "A1 TT" not found in rating.xlsx')
        valueRow = [c.value for c in rows[1]]
        expected = [('A1 TT', 0), ('A2 C', 1), ('A2 T', 0), ('A3 C', 1), ('A3 T', -1), ('A4 ST', 1), ('A4 TT', 0)]
        end = ix + len(expected) + 1
        titles = titleRow[ix:end]
        values = valueRow[ix:end]
        assertEqual(
            expected,
            list(zip(titles, values))
        )

        # plagiarism
        # todo

        print('### export ###')
        shell.run([checkAssignments, 'export'])
        assertExists(barFoo + 'POINTS.txt')
        assertExists('rating.csv')
        assertExists('feedback.zip')
        zip = zipfile.ZipFile('feedback.zip')
        fileName = 'Bar Foo_1234_assignsubmission_file_/COMMENTS.txt'
        if fileName not in zip.namelist():
            abort(f'{fileName} not in zip')
        zip.close()
print()

with shell.tempDir(onException=False) as tmp:
    print(f'tmp={tmp}')
    shell.cp(shell.pjoin(topDir, 'test-data'), tmp)
    with shell.workingDir(shell.pjoin(tmp, 'test-data/submissions')):

        print('### prepare ###')
        shell.run([checkAssignments, 'prepare', '../rating-moodle.csv'])
        assertExists('rating.xlsx')
        barFoo = 'Bar Foo_1234_assignsubmission_file_/'
        assertExists(barFoo + 'assignment_01.py')
        assertExists(barFoo + 'COMMENTS.txt')
