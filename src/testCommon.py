from __future__ import annotations
import shell
from config import Assignment
from typing import Literal
from ansi import *

TestKind = Literal['student', 'instructor']

def runTestScriptIfExisting(assignmentId: int, kind: TestKind):
    if kind == 'student':
        script = "../run-student-tests.sh"
    else:
        script = "../run-tests.sh"
    if shell.isFile(script):
        print(blue(f"Running test script {script}"))
        cmdList = [script, str(assignmentId)]
        return shell.run(['timeout', '--signal', 'KILL', '10'] + cmdList, onError='ignore',
                           captureStdout=True, stderrToStdout=True)
    else:
        return None
