import shell
import os
import zipfile

def readBinaryFile(name):
    with open(name, 'rb') as f:
        return f.read()

def readFile(name):
    with open(name, 'r', encoding='utf-8') as f:
        return f.read()

def writeFile(name, content):
    with open(name, 'w', encoding='utf-8') as f:
        f.write(content)

def writeBinaryFile(name, content):
    with open(name, 'wb') as f:
        f.write(content)

def collectSubmissionDirs(config, baseDir=None):
    if baseDir is None:
        baseDir = config.baseDir
    result = []
    for x in shell.ls(baseDir, '*'):
        if shell.isDir(x) and config.isSubmissionDir(shell.basename(x)):
            result.append(x)
    return sorted(result)

def collectSubmissionFiles(config, d):
    globs = set([a.submissionFileGlob for a in config.assignments])
    files = []
    for g in globs:
        files = files + shell.run(['find', d, '-name', g], captureStdout=shell.splitLines).stdout
    return sorted(files)

def findSubmissionDirForId(config, x):
    """
    Returns the submission directory for a student with ID x.
    Prefers _file_ directory over _onlinetext_.
    """
    dirs = [d for d in shell.ls(config.baseDir, f'*_{x}_*') if shell.isdir(d)]
    if len(dirs) == 0:
        return None
    for d in dirs:
        if d.endswith('_file_'):
            return d
    return dirs[0]

def parseSubmissionDir(cfg, d):
    """
    Returns a pair (name, id) where id is either the loginname or the matrikel of the student.
    """
    x = shell.basename(d)
    if not x:
        x = d
    x = stripLeadingSlash(x)
    x = stripTrailingSlash(x)
    if not cfg.isSubmissionDir(x):
        raise ValueError(f'Invalid submission directory: {x}')
    comps = x.split('_')
    if len(comps) == 0:
        raise ValueError(f'Invalid submission directory: {x}')
    elif len(comps) == 1:
        return (x, x)
    else:
        return (comps[0], comps[1])

def stripSlashes(x):
    if not x:
        return x
    x = x.strip()
    if x.endswith('/'):
        return stripSlashes(x[:-1])
    else:
        return x

def hasSameContent(f1, f2):
    c1 = readBinaryFile(f1)
    c2 = readBinaryFile(f2)
    return c1 == c2

# Copies srcDir/path to targetDir/path, but only if targetDir/path does not exist.
# Outputs a warning if targetDir/path exists but is not identical to srcDir/path
def copyFileIfNotExists(srcDir, path, targetDir):
    srcPath = shell.pjoin(srcDir, path)
    if not shell.isFile(srcPath):
        raise IOError(f'{srcPath} must be a file')
    tgtPath = shell.pjoin(targetDir, path)
    if shell.isDir(tgtPath):
        raise IOError(f'{tgtPath} must not be a directory')
    shell.mkdir(shell.dirname(tgtPath), createParents=True)
    if shell.isFile(tgtPath):
        if not hasSameContent(srcPath, tgtPath):
            raise IOError(f'Target file {tgtPath} already exists with content different than in {srcPath}')
    else:
        shell.cp(srcPath, tgtPath)

def zipDirs(zipPath, dirs, excludeDirs=[]):
    zf = zipfile.ZipFile(zipPath, 'w', zipfile.ZIP_DEFLATED)
    for d in dirs:
        for dirpath, dirs, files in os.walk(d):
            for x in excludeDirs:
                try:
                    dirs.remove(x)
                except ValueError:
                    pass
            for f in files:
                zf.write(os.path.join(dirpath, f),
                         os.path.relpath(os.path.join(dirpath, f),
                                         os.path.join(d, '..')))
    zf.close()

def stripLeadingSlash(x):
    if x.startswith('/'):
        return stripLeadingSlash(x[1:])
    return x

def stripTrailingSlash(x):
    if x.endswith('/'):
        return stripTrailingSlash(x[:-1])
    return x

def stringAfterLastOccurrenceOf(s: str, part: str):
    i = s.rindex(part)
    return s[i + len(part):]

def fileEquals(path1: str, path2: str):
    if shell.isFile(path1) and shell.isFile(path2):
        return readBinaryFile(path1) == readBinaryFile(path2)
    else:
        return False

def dirEquals(path1: str, path2: str):
    if shell.isDir(path1) and shell.isDir(path2):
        d1 = dict([(shell.basename(x), x) for x in shell.ls(path1, '*')])
        d2 = dict([(shell.basename(x), x) for x in shell.ls(path2, '*')])
        if d1.keys() != d2.keys():
            return False
        for k, v1 in d1.items():
            v2 = d2[k]
            if not fileSystemItemEquals(v1, v2):
                return False
        return True
    else:
        return False

def fileSystemItemEquals(path1: str, path2: str):
    if fileEquals(path1, path2):
        return True
    if dirEquals(path1, path2):
        return True
    else:
        return False
