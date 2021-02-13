from ownLogging import *
from utils import *
import tempfile
import zipfile

def unzip(config):
    submissionDirs = collectSubmissionDirs(config)
    for d in submissionDirs:
        zipFiles = shell.ls(d, '*.zip')
        if len(zipFiles) == 0:
            print(f'No zip-file in {d}')
            continue
        elif len(zipFiles) > 1:
            warn(f"More than one zip-file found in ${d}, don't know what to do")
            continue
        zipFile = zipFiles[0]
        with tempfile.TemporaryDirectory(dir='/tmp') as tmpDir:
            zipfile.ZipFile(zipFile).extractall(tmpDir)
            extractedFiles = shell.ls(tmpDir, '*')
            extractedFiles = [f for f in extractedFiles if shell.basename(f) != '__MACOSX']
            # strip away one directory level if the zip-archive contains a single directory
            # at the top.
            if len(extractedFiles) == 1:
                f = extractedFiles[0]
                if shell.isDir(f):
                    extractedFiles = shell.ls(f, '*')
            if shell.basename(zipFile) in [shell.basename(f) for f in extractedFiles]:
                warn(f"Zip-file {zipFile} contains another zip-file with the same name. Cannot continue.")
                continue
            for f in extractedFiles:
                target = shell.pjoin(d, shell.basename(f))
                if not shell.exists(target):
                    shell.mv(f, target)
            print(f'Successfully extracted {zipFile}')
