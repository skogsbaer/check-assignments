import shell
import utils
import ansi
import os
from ownLogging import verbose

class Mode:
    merged = 'merged'
    separate = 'separate'

resultDir = 'jplag-results'
DEFAULT_MIN_SCORE = 95

class JplagArgs:
    def __init__(self, mode, minScore=DEFAULT_MIN_SCORE, printDiff=False):
        if mode not in [Mode.merged, Mode.separate]:
            utils.abort(f'Invalid mode for jplag plagiarism detection: mode must be {Mode.merged} or {Mode.separate}')
        self.mode = mode
        self.minScore = minScore
        self.printDiff = printDiff

def runJplag(opts, args, file=None):
    jarFile = shell.pjoin(shell.dirname(__file__), '..', 'resources',
                'jplag-2.12.1-SNAPSHOT-jar-with-dependencies.jar')
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
                    if file and args.printDiff and score >= 99.99999999999999999:
                        printDiff(l, file)
        elif 'Writing results to' in l:
            print(ansi.blue(l + "/index.html"))
        else:
            verbose(l)
    if not haveMinScore:
        print(f'No submissions detected with similaries >= {args.minScore}')

def printDiff(l, file):
    l = l.replace('Comparing ', '')
    l = l[:l.rindex(':')]
    idx = -1
    while True:
        try:
            idx = l.index('-', idx + 1)
        except ValueError:
            return
        d1 = l[:idx]
        d2 = l[idx+1:]
        fst = os.path.join(d1, file)
        snd = os.path.join(d2, file)
        if os.path.isfile(fst) and os.path.isfile(snd):
            r = shell.run(['diff', '-u', fst, snd], onError='ignore', captureStdout=True)
            out = r.stdout
            outLines = out.split('\n')
            changes = 0
            for l in outLines:
                if l.startswith('+') or l.startswith('-'):
                    changes = changes + 1
            maxLines = 12
            if changes > maxLines:
                print(f'Diff longer than {maxLines} lines')
            elif r.exitcode == 0:
                print(ansi.red(f'File {file} is identical in {d1} and {d2}'))
            else:
                print(out)
            return


def runJplagMerged(lang, kind, ext, args):
    print()
    print(ansi.green(f'Running jplag for all assignments of kind {kind}'))
    runJplag(['-r', shell.pjoin(resultDir, kind), '-s', '-l', lang, '-p', ext, '.'], args)

def runJplagForFile(lang, kind, file, args):
    print()
    print(ansi.green(f'Running jplag for file {file}'))
    runJplag(['-r', shell.pjoin(resultDir, kind, file), '-s', '-l', lang, '-p', file, '.'], args, file)

def jplag(cfg, args):
    if shell.isDir(resultDir):
        shell.rmdir(resultDir, recursive=True)
    lang = ''
    assDict = cfg.assignmentsGroupedByKind
    for kind, ass in assDict.items():
        if kind == 'python':
            lang = 'python3'
        elif kind == 'java':
            lang = 'java19'
        else:
            print(f'Cannot run jplag for {kind}')
        if args.mode == Mode.merged:
            runJplagMerged(lang, kind, ass[0].submissionFileExt, args)
        elif args.mode == Mode.separate:
            for a in ass:
                runJplagForFile(lang, kind, a.getMainFile(''), args)
