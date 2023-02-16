from __future__ import annotations
from config import *
from ansi import *
from ownLogging import *
from testCommon import *
import sys

@dataclass
class Result:
    runError: bool
    testsTotal: int
    testsFailed: int

    def ratio(self):
        if self.testsTotal == 0:
            return -1
        return float(self.testsTotal - self.testsFailed) / self.testsTotal

    @property
    def ok(self):
        return self.testsFailed == 0 and not self.runError
    @staticmethod
    def __parseWyppResult(prefix: str, s: str):
        runError = 'Traceback (most recent call last):' in s
        r1 = re.compile(f'^{prefix}' + r'\s*(\d+) Tests, (\d+) Fehler')
        r2 = re.compile(f'^{prefix}' + r'\s*(\d+) Tests, alle erfolgreich')
        for l in s.split('\n'):
            m1 = r1.match(l)
            if m1:
                total = int(m1.group(1))
                fail = int(m1.group(2))
                return Result(runError, total, fail)
            m2 = r2.match(l)
            if m2:
                total = int(m2.group(1))
                return Result(runError, total, 0)
    @staticmethod
    def __parseUnitResult(prefix: str, s: str):
        # Ran 3 tests in 0.000s
        # FAILED (errors=1)
        # FAILED (failures=1, errors=1)
        # OK
        total = -1
        errors = 0
        failures = 0
        skipped = 0
        r = re.compile('^Ran (\\d+) test')
        def getKv(l, k):
            r = re.compile(f'{k}=(\\d+)')
            m = r.search(l)
            if m:
                return int(m.group(1))
            else:
                return 0
        for l in s.split('\n'):
            l = l.strip()
            m = r.match(l)
            if m:
                total = int(m.group(1))
            if l.startswith('FAILED'):
                errors = getKv(l, 'errors')
                failures = getKv(l, 'failures')
                skipped = getKv(l, 'skipped')
        if total > 0:
            return Result(False, total - skipped, errors + failures)
    def parseResult(prefix: str, s: str):
        r = Result.__parseWyppResult(prefix, s)
        if r:
            return r
        r = Result.__parseUnitResult(prefix, s)
        if r:
            return r
        runError = 'Traceback (most recent call last):' in s
        return Result(runError, 0, 0)

def runPythonTests(ctx, studentDir: str, assignment: Assignment):
    with shell.workingDir(studentDir):
        result = runTestScriptIfExisting(assignment, 'instructor', captureStdout=False,
                                        stderrToStdout=False)
    if result is None:
        _runPythonTest(ctx, studentDir, assignment, str(assignment.id), testKindStudent,
            mainFile=assignment.getMainFile(studentDir),
            testFile=None,
            logFile=assignment.studentOutputFile(studentDir))
        tests = assignment.tests
        for t in tests:
            _runPythonTest(ctx, studentDir, assignment, t.id, testKindTutor,
                mainFile=assignment.getMainFile(studentDir),
                testFile=t.file,
                logFile=t.outputFile(studentDir))


def _runPythonTest(ctx, studentDir: str, assignment: Assignment, testId: str, testKind: TestKind,
                   mainFile: str, testFile: Optional[str], logFile: str):
    cfg = ctx.cfg
    wyppDir = cfg.wyppDir
    if not wyppDir:
        abort(f'Directory for write-your-python program must be set for python tests')
    if not shell.isDir(wyppDir):
        abort(f'Directory {wyppDir} does not exist.')
    progArgs = [
        'timeout',
        '15',
        sys.executable,
        shell.pjoin(wyppDir, 'python/src/runYourProgram.py')
    ]
    if testFile:
        args = ['--test-file', testFile, '--check', mainFile]
    else:
        args = ['--check', mainFile]
    runArgs = progArgs + args
    verbose(f'Running {runArgs}')
    with shell.createTee([shell.TEE_STDOUT, logFile]) as tee:
        runRes = shell.run(runArgs, onError='ignore', stderrToStdout=True, captureStdout=tee,
                           env={'PYTHONPATH': f'{wyppDir}/python/site-lib'})
    output = utils.readFile(logFile)
    result = Result.parseResult('' if testKind == testKindStudent else 'Tutor:', output)
    if runRes.exitcode == 124:
        print(red(f'Test {testId} timeout'))
    if result.ok:
        print(green(f'Test {testId} OK'))
    else:
        print(red(f'Test {testId} FAILED, see above'))
    prefix = 'S' if testKind == testKindStudent else ''
    ctx.storeTestResultInSpreadsheet(studentDir, assignment, testId, [prefix + 'C'],
        0 if result.runError else 1)
    ctx.storeTestResultInSpreadsheet(studentDir, assignment, testId, [prefix + 'T'], result.ratio())
