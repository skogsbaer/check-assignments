#!/usr/bin/env python

import sys
import os
import zipfile
thisDir = os.path.dirname(__file__)
topDir = os.path.join(thisDir, '..')
sys.path.insert(0, os.path.join(topDir, 'src'))
import shell

checkAssignments = shell.abspath(shell.pjoin(topDir, 'check-assignments'))
if sys.platform == 'win32':
    checkAssignments = checkAssignments + ".bat"

def abort(msg):
    sys.stderr.write(msg + '\n')
    sys.exit(1)

def assertExists(path):
    if not shell.isFile(path):
        abort(f'File {path} does not exist')

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

        print('### addComment ###')
        shell.run([checkAssignments, 'addComment'])
        assertExists(barFoo + 'COMMENTS.txt')

        print('### tests ###')
        shell.run([checkAssignments, 'runTests'])

        print()
        print('NOTE: the python test should fail with "AssertionError: 41 != 42"')
        print('NOTE: the java test should fail with "org.opentest4j.AssertionFailedError: expected: <1> but was: <0>"')

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
