import shell
from utils import *
from ownLogging import *
from dataclasses import dataclass
from config import Config

@dataclass
class FixFilenamesArgs:
    moveUp: bool

def withFilenames(config, what, action):
    submissionDirs = collectSubmissionDirs(config)
    for d in submissionDirs:
        student = shell.basename(d)
        verbose(f'{what} filenames for student {student}')
        for k, assList in config.assignmentsGroupedByKind.items():
            ass = assList[0]
            files = set([shell.basename(f) for f in shell.ls(d, ass.submissionFileGlob)])
            expected = set([shell.basename(f) for a in assList if (f := a.getMainFile(student)) is not None])
            missing = expected - files
            superfluous = files - expected
            found = files.intersection(expected)
            verbose(f'{what} filenames for student {student} and kind {k}. files={files}, expected={expected}, missing={missing}, superflous={superfluous}, found={found}')
            action(student, k, d, found, missing, superfluous)

def checkFilenames(config):
    result = {}
    def action(student, k, d, found, missing, superfluous):
        if len(missing) > 0:
            if len(superfluous) > 0:
                warn(f'Student {student} misses {k} assignments {missing} but has the following extra files: {superfluous}')
                result[k] = 'missing-but-extra'
            else:
                verbose(f'Student {student} misses {k} assignments {missing} and there are no extra files.')
                result[k] = 'missing'
        else:
            verbose(f'Student {student} has all {k} assignments')
            result[k] = 'ok'
    withFilenames(config, "checking", action)
    return result

def moveUp(config: Config):
    submissionDirs = collectSubmissionDirs(config)
    for d in submissionDirs:
        student = shell.basename(d)
        dirs = [x for x in shell.ls(d, '*') if shell.isDir(x) and not shell.basename(x).startswith('.')]
        if len(dirs) == 1:
            subDir = dirs[0]
            print(f'Moving content of {shell.basename(subDir)} one level up for {student}')
            for x in shell.ls(subDir, '*'):
                target = shell.pjoin(d, shell.basename(x))
                verbose(f'{x} -> {target}')
                shell.mv(x, target)
            shell.rmdir(subDir)
        else:
            names = [shell.basename(x) for x in dirs]
            print(f'Could not move content up one level for {student}, subdirs: {names}')

def fixFilenames(config, args: FixFilenamesArgs):
    if args.moveUp:
        moveUp(config)
        return
    def action(student, k, d, found, missing, superfluous):
        for m in missing:
            candidates = []
            for s in superfluous:
                if s.endswith(m) or len(superfluous) == 1:
                   candidates.append(s)
            verbose(f'Fixing filenames for student {student} and kind {k}. candidates={candidates}')
            if len(candidates) > 1:
                print(f'Cannot fix name of assignment {m} for {student} because there is more than one matching file')
            elif len(candidates) == 1:
                c = candidates[0]
                src = shell.pjoin(d, c)
                tgt = shell.pjoin(d, m)
                verbose(f'Renaming {src} to {tgt}')
                shell.mv(src, tgt)
    withFilenames(config, "fixing", action)
