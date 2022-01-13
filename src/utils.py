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

def collectSubmissionDirs(config, baseDir=None, includeBoth=False):
    if baseDir is None:
        baseDir = config.baseDir
    dirs1 = shell.ls(baseDir, config.submissionDirGlob)
    dirs2 = []
    if includeBoth:
        dirs2 = shell.ls(config.baseDir, config.submissionDirTextGlob)
    result = [d for d in dirs1 + dirs2 if shell.isdir(d)]
    return sorted(result)

def collectSubmissionFiles(config, d):
    globs = set([a.submissionFileGlob for a in config.assignments])
    files = []
    for g in globs:
        files = files + shell.ls(d, g)
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
    x = shell.basename(d)
    if not x:
        x = d
    x = stripLeadingSlash(x)
    x = stripTrailingSlash(x)
    suf = cfg.submissionDirSuffix
    if x.endswith(suf):
        x = x[:-len(suf)]
    try:
        i = x.rindex('_')
    except ValueError:
        raise ValueError(f'Invalid submission directory: {x}')
    if i > 0 and i < len(x) - 1:
        name = x[:i]
        matrikel = x[i+1:]
        return (name, matrikel)
    else:
        raise ValueError(f'Invalid submission directory: {x}')

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

def zipDirs(zipPath, dirs):
    zf = zipfile.ZipFile(zipPath, 'w', zipfile.ZIP_DEFLATED)
    for d in dirs:
        for root, dirs, files in os.walk(d):
            for f in files:
                zf.write(os.path.join(root, f),
                         os.path.relpath(os.path.join(root, f),
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
