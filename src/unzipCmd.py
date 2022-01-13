from ownLogging import *
from utils import *
import tempfile
import zipfile

STOP_DIRS = ['src']
IGNORE_DIRS = ['bin', 'build']

def getExtractedFiles(d):
    extractedFiles = [f for f in shell.ls(d, '*') if shell.basename(f) != '__MACOSX']
    # strip away one directory level if the zip-archive contains a single directory
    # at the top and the name of the directory is not in STOP_DIRS
    if len(extractedFiles) == 1:
        f = extractedFiles[0]
        if shell.isDir(f) and shell.basename(f) not in STOP_DIRS:
            return getExtractedFiles(f)
    return [f for f in extractedFiles if shell.basename(f) not in IGNORE_DIRS]

def unzip(config):
    submissionDirs = collectSubmissionDirs(config)
    for d in submissionDirs:
        zipFiles = shell.ls(d, '*.zip', '*.ZIP')
        if len(zipFiles) == 0:
            print(f'No zip-file in {d}')
            continue
        elif len(zipFiles) > 1:
            warn(f"More than one zip-file found in ${d}, don't know what to do")
            continue
        zipFile = zipFiles[0]
        sysTempDir = tempfile.gettempdir()
        with tempfile.TemporaryDirectory(dir=sysTempDir) as tmpDir:
            shell.run(['unzip', zipFile, '-d', tmpDir])
            extractedFiles = getExtractedFiles(tmpDir)
            if shell.basename(zipFile) in [shell.basename(f) for f in extractedFiles]:
                warn(f"Zip-file {zipFile} contains another zip-file with the same name. Cannot continue.")
                continue
            for f in extractedFiles:
                target = shell.pjoin(d, shell.basename(f))
                if not shell.exists(target):
                    shell.mv(f, target)
            print(f'Successfully extracted {zipFile} to directory {d}')
