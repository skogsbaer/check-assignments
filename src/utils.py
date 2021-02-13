import shell

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
    files = shell.ls(d, config.submissionFileGlob)
    expected = set(config.assignments)
    return sorted([f for f in files if shell.basename(f) in expected])

def collectTestFiles(config):
    if config.testDir is None:
        return None
    files = shell.ls(config.testDir, config.submissionFileGlob)
    return files

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

def stripSlashes(x):
    if not x:
        return x
    x = x.strip()
    if x.endswith('/'):
        return stripSlashes(x[:-1])
    else:
        return x
