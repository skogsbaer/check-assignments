from __future__ import annotations
import shell
from utils import *
from ansi import *
from ownLogging import *

def runJavaTests(cfg: Config, args: TestArgs, studentDir: str, assignment: Assignment):
    gradleProps = {
        'testFilter': assignment.getValue('test-filter', ''),
        'testDir': cfg.testDir,
        'studentDir': studentDir
    }
    gradlePropArgs = []
    for k, v in gradleProps.items():
        gradlePropArgs.append(f'-P{k}={v}')
    print()
    with shell.workingDir(cfg.baseDir):
        if not shell.isFile('build.gradle'):
            abort(f'No build.gradle file in {cfg.baseDir}, aborting')
        if not assignment.hasTests:
            gradleCmd = 'compileJava'
        else:
            gradleCmd = 'test'
        cmd = [cfg.gradlePath] + gradlePropArgs + [gradleCmd, '--rerun-tasks']
        print(f'Executing {" ".join(cmd)}')
        logFileName = shell.pjoin(studentDir, f'OUTPUT_{assignment.id}.txt')
        with open(logFileName, 'w') as logFile:
            tee = shell.createTee([sys.stdout, logFile])
            result = shell.run(cmd, onError='ignore', stderrToStdout=True, captureStdout=tee)
    if result.exitcode == 0:
        print(green(f'Tests for {assignment.id} OK'))
    else:
        print(red(f'Tests for {assignment.id} FAILED, see above'))
