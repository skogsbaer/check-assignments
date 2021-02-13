import pycode_similar
import difflib
from ownLogging import *
from utils import *
import tempfile

def checkForPlagiarismByDiff(config, f1, f2):
    s1 = readFile(f1)
    s2 = readFile(f2)
    if s1 == s2:
        print(f'Plagiarism detected: {f1} and {f2} are identical')
        return True
    else:
        lines = list(difflib.unified_diff(s1, s2, fromfile=f1, tofile=f2))
        c1 = 0
        c2 = 0
        for l in lines:
            if l.startswith('-') and not l.startswith('---'):
                c1 += 1
            if l.startswith('+') and not l.startswith('+++'):
                c2 += 1
        if c1 < 3 and c2 < 3:
            diffOut = ''.join(lines)
            print(f'Plagiarism detected: {f1} and {f2} are very similar:\n{diffOut}')
            return True
        else:
            return False

def checkPlagiarismForFiles(config, args, f1, f2):
    if args.threshold > 99:
        return checkForPlagiarismByDiff(config, f1, f2)
    c1 = readFile(f1)
    c2 = readFile(f2)
    if c1 == c2:
        print(f'Plagiarism detected: {f1} and {f2} are identical')
        return True
    try:
        res = pycode_similar.detect([c1, c2], diff_method=pycode_similar.UnifiedDiff, keep_prints=True, module_level=True)
    except Exception as e:
        msg = f'Cannot check plagiarism between {f1} and {f2}: ' + str(e)
        if isinstance(e, SyntaxError):
            verbose(msg)
        else:
            warn(msg)
        return
    if len(res) == 0:
        warn(f'No plagiarism result found for {f1} and {f2}')
    if len(res) > 1:
        warn(f'More than one plagiarism result found for {f1} and {f2}')
    (_, x) = res[0]
    sumPlagiarismFactor, sumPlagiarismCount, sumTotalCount = pycode_similar.summarize(x)
    sumPlagiarismPercent = sumPlagiarismFactor * 100
    msg = '{:.2f} % ({}/{}) of ref code structure is plagiarized by candidate.'.format(
        sumPlagiarismPercent,
        sumPlagiarismCount,
        sumTotalCount,
    )
    if sumPlagiarismPercent >= args.threshold:
        print(f'Detected plagiarism between {f1} and {f2}: {msg}')
        if args.verbose:
            shell.run(['diff', '-u', f1, f2], onError='ignore')
        return True
    else:
        verbose(f'No plagiarism between {f1} and {f2}')
        return False

class PlagiarismArgs:
    def __init__(self, threshold, ignore, verbose):
        self.threshold = threshold
        self.verbose = verbose
        if ignore:
            self.ignore = [s.strip() for s in ignore.split(',')]
        else:
            self.ignore = []

def checkPlagiarism(config, args):
    submissionDirs = collectSubmissionDirs(config)
    suspiciousFiles = []
    for i, d1 in enumerate(submissionDirs):
        for d2 in submissionDirs[i+1:]:
            fs1 = collectSubmissionFiles(config, d1)
            for f1 in fs1:
                base1 = shell.basename(f1)
                f2 = shell.pjoin(d2, base1)
                if shell.isfile(f2) and base1 not in args.ignore:
                    verbose(f'Checking {f1} against {f2}')
                    res = checkPlagiarismForFiles(config, args, f1, f2)
                    if res:
                        suspiciousFiles.append((f1, f2))
    if suspiciousFiles:
        shellScriptLines = ['tool=opendiff']
        for i, (f1, f2) in enumerate(suspiciousFiles):
            shellScriptLines.append(f"$tool '{f1}' '{f2}'")
            if i < len(suspiciousFiles) - 1:
                shellScriptLines.append("echo 'Continue?'; read")
        with tempfile.NamedTemporaryFile(mode='w', prefix='plagiarism_', suffix='.sh', delete=False) as f:
            f.write('\n'.join(shellScriptLines))
            print(f'Command for diffing suspicious files: bash {f.name}')
