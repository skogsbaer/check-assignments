import shell
import utils
import ansi

class Mode:
    merged = 'merged'
    separate = 'separate'

resultDir = 'jplag-results'
minScore = 95

class JplagArgs:
    def __init__(self, mode):
        if mode not in [Mode.merged, Mode.separate]:
            utils.abort(f'Invalid mode for jplag plagiarism detection: mode must be {Mode.merged} or {Mode.separate}')
        self.mode = mode

def runJplag(opts):
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
                print(l)
            if i >= 0:
                score = float(l[i+1:].strip())
                if score > minScore:
                    haveMinScore = True
                    print(ansi.red(l))
        elif 'Writing results to' in l:
            print(ansi.blue(l + "/index.html"))
        else:
            print(l)
    if not haveMinScore:
        print(f'No submissions detected with similaries higher than {minScore}')

def runJplagMerged(lang, kind, ext):
    print()
    print(ansi.green(f'Running jplag for all assignments of kind {kind}'))
    runJplag(['-r', shell.pjoin(resultDir, kind), '-s', '-l', lang, '-p', ext, '.'])

def runJplagForFile(lang, kind, file):
    print()
    print(ansi.green(f'Running jplag for file {file}'))
    runJplag(['-r', shell.pjoin(resultDir, kind, file), '-s', '-l', lang, '-p', file, '.'])

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
            runJplagMerged(lang, kind, ass[0].submissionFileExt)
        elif args.mode == Mode.separate:
            for a in ass:
                runJplagForFile(lang, kind, a.getMainFile(''))
