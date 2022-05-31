import shell
import utils
import ansi
import os
from ownLogging import verbose, abort

class Mode:
    merged = 'merged'
    separate = 'separate'

resultDir = 'jplag-results'
DEFAULT_MIN_SCORE = 95

class JplagArgs:
    def __init__(self, mode, minScore=DEFAULT_MIN_SCORE, printDiff=False):
        if mode not in [Mode.merged, Mode.separate]:
            abort(f'Invalid mode for jplag plagiarism detection: mode must be {Mode.merged} or {Mode.separate} but is {mode}')
        self.mode = mode
        self.minScore = minScore
        self.printDiff = printDiff

def runJplag(opts, args, fileGlob=None):
    jarName = 'jplag-3.0.0-jar-with-dependencies.jar'
    jarFile = shell.pjoin(shell.dirname(__file__), '..', 'resources', jarName)
    print('Running jplag, this might take a while ...')
    res = shell.run(['java', '-jar', jarFile] + opts, captureStdout=True, stderrToStdout=True)
    haveMinScore = False
    for l in res.stdout.split('\n'):
        if 'no viable alternative at input' in l:
            pass
        elif 'nothing to parse for submission' in l:
            pass
        elif l.startswith('Comparing '):
            i = -1
            try:
                i = l.rindex(':')
            except ValueError:
                verbose(l)
            if i >= 0:
                score = float(l[i+1:].strip())
                if score >= args.minScore:
                    haveMinScore = True
                    print(ansi.red(l))
                    if args.printDiff and score >= 99.99999999999999999:
                        printDiffForJplag(l, fileGlob)
        elif 'Writing results to' in l:
            print(ansi.blue(l + "/index.html"))
        else:
            verbose(l)
    if not haveMinScore:
        print(f'No submissions detected with similaries >= {args.minScore}')

def numberOfLines(file):
    return len(open(file).readlines())

def printDiff(fst, snd, msg, printNoteForLongDiff=True):
    cmd = f"diff -u '{fst}' '{snd}'"
    r = shell.run(cmd, onError='ignore', captureStdout=True)
    out = r.stdout
    outLines = out.split('\n')
    changes = 0
    for l in outLines:
        if l.startswith('+') or l.startswith('-'):
            changes = changes + 1
    n = min(numberOfLines(fst), numberOfLines(snd))
    maxLines = max(12, int(n / 20.0)) # 5% of the minimal number of lines
    if changes > maxLines:
        if printNoteForLongDiff:
            print(f'Diff longer than {maxLines} lines: {cmd}')
    elif r.exitcode == 0:
        print(ansi.red(msg))
    else:
        print(out)

def findFiles(dir, glob):
    with shell.workingDir(dir):
        l = shell.run(['find', '.', '-name', glob], captureStdout=shell.splitLines).stdout
        return [utils.stripLeading(x, './') for x in l]

def printDiffForJplag(l, fileGlob):
    l = l.replace('Comparing ', '')
    l = l[:l.rindex(':')]
    idx = -1
    dir1 = None
    dir2 = None
    while True:
        try:
            idx = l.index('-', idx + 1)
        except ValueError:
            break
        d1 = l[:idx]
        d2 = l[idx+1:]
        if os.path.isdir(d1) and os.path.isdir(d2):
            dir1 = d1
            dir2 = d2
            break
    if dir1 is None or dir2 is None:
        return
    files1 = findFiles(dir1, fileGlob)
    files2 = findFiles(dir2, fileGlob)
    for file in set(files1 + files2):
        fst = os.path.join(dir1, file)
        snd = os.path.join(dir2, file)
        if os.path.isfile(fst) and os.path.isfile(snd):
            printDiff(fst, snd, f'File {file} is identical in {d1} and {d2}')


def runJplagMerged(lang, kind, ext, args):
    print()
    print(ansi.green(f'Running jplag for all assignments of kind {kind}'))
    runJplag(['-r', shell.pjoin(resultDir, kind), '-l', lang, '-p', ext, '.'], args, '*' + ext)

def runJplagForFile(lang, kind, file, args):
    print()
    print(ansi.green(f'Running jplag for file {file}'))
    runJplag(['-r', shell.pjoin(resultDir, kind, file), '-l', lang, '-p', file, '.'], args, file)

def jplag(cfg, args):
    if shell.isDir(resultDir):
        shell.rmdir(resultDir, recursive=True)
    lang = ''
    assDict = cfg.assignmentsGroupedByKind
    files = set()
    for kind, ass in assDict.items():
        if kind == 'python':
            lang = 'python3'
        elif kind == 'java':
            lang = 'java'
        else:
            print(f'Cannot run jplag for {kind}')
            continue
        if args.mode == Mode.merged:
            runJplagMerged(lang, kind, ass[0].submissionFileExt, args)
        elif args.mode == Mode.separate:
            for a in ass:
                f = a.getMainFile('')
                if f and f not in files:
                    files.add(f)
                    runJplagForFile(lang, kind, a.getMainFile(''), args)
