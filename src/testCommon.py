from __future__ import annotations
import shell
from config import Assignment
from typing import Literal
from ansi import *

TestKind = Literal['student', 'instructor']

# Runs a custom test script. The test script is named
# "run-student-tests.sh" (for student tests) or "run-tests.sh"
# (for tutor tests). It must be placed in the toplevel directory.
# The script gets the assignment ID and the value the scriptArgs
# property of the assignment from check.yml.
def runTestScriptIfExisting(assignment: Assignment, kind: TestKind,
                            captureStdout=True, stderrToStdout=True):
    if kind == 'student':
        scriptBase = "../run-student-tests"
    else:
        scriptBase = "../run-tests"
    exts = [".sh", ".py", ""]
    for e in exts:
        script = scriptBase + e
        if shell.isFile(script):
            print(blue(f"Running test script {script}"))
            cmdList = [script, str(assignment.id)]
            timeout = []
            if assignment.timeout:
                timeout = ['timeout', '--signal', 'KILL', str(assignment.timeout)]
            args = assignment.scriptArgs
            return shell.run(timeout + cmdList + args, onError='ignore',
                               captureStdout=captureStdout, stderrToStdout=stderrToStdout)
    return None
