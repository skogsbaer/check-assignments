import shell
import utils

extensions = ['.java', '.py', '.hs']

def fixEncoding(cfg):
    dirs = utils.collectSubmissionDirs(cfg)
    args = []
    for e in extensions:
        if args:
            args.append('-o')
        args.append('-name')
        args.append('*' + e)
    for d in dirs:
        files = shell.run(['find', d] + args, captureStdout=shell.splitLines).stdout
        for f in files:
            fix(f)

replacements = ['ä', 'ö', 'ü', 'Ä', 'Ö', 'Ü', 'ß']

def fix(path):
    bytesOrig = open(path, 'rb').read()
    bytes = bytesOrig
    for r in replacements:
        bytes = bytes.replace(r.encode('iso-8859-1'), r.encode('utf-8'))
    if bytes != bytesOrig:
        open(path, 'wb').write(bytes)
        print(f'Fixed encoding of {path}')
