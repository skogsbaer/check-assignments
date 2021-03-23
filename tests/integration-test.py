#!/usr/bin/env python

import sys
import os
thisDir = os.path.dirname(__file__)
topDir = os.path.join(thisDir, '..')
sys.path.insert(0, os.path.join(topDir, 'src'))
import shell

checkAssignments = shell.abspath(shell.pjoin(topDir, 'src', 'check.py'))

def abort(msg):
    sys.stderr.write(msg + '\n')
    sys.exit(1)

def assertExists(path):
    if not shell.isFile(path):
        abort(f'File {path} does not exist')

with shell.tempDir(onException=False) as tmp:
    print(f'tmp={tmp}')
    shell.cp(shell.pjoin(topDir, 'test-data'), tmp)
    shell.cd(tmp)
    shell.cd('test-data/submissions')

    print('### import ###')
    shell.run(['python3', checkAssignments, 'import', '../rating-moodle.csv'])
    assertExists('rating.xlsx')

    print('### unzip ###')
    barFoo = 'Bar Foo_1234_assignsubmission_file_/'
    shell.run(['python3', checkAssignments, 'unzip'])
    assertExists(barFoo + 'assignment_01.py')

    print('### addComment ###')
    shell.run(['python3', checkAssignments, 'addComment'])
    assertExists(barFoo + 'COMMENTS.txt')

    print('### tests ###')
    shell.run(['python3', checkAssignments, 'runTests'])

    # plagiarism
    # todo

    print('### export ###')
    shell.run(['python3', checkAssignments, 'export'])
    assertExists(barFoo + 'POINTS.txt')
    assertExists('rating.csv')
    assertExists('feedback.zip')
