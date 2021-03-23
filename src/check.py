import shell
import argparse
import zipfile
import fnmatch
import os
import shutil
import itertools
import exportCmd
import plagiarismCmd
import testCmd
import importCmd
import unzipCmd
from ownLogging import *
from utils import *
from config import *

def checkFilenames(config):
    submissionDirs = collectSubmissionDirs(config)
    for d in submissionDirs:
        student = shell.basename(d)
        files = set([shell.basename(f) for f in shell.ls(d, config.submissionFileGlob)])
        expected = set(config.assignments)
        missing = expected - files
        superfluous = files - expected
        if len(missing) > 0:
            if len(superfluous) > 0:
                warn(f'{student} misses assignments {missing} but has the following extra files: {superfluous}')
            else:
                verbose(f'{student} misses assignments {missing} and there are no extra files.')
        else:
            verbose(f'{student} has all assignments')

def fixFilenames(config):
    submissionDirs = collectSubmissionDirs(config)
    for d in submissionDirs:
        student = shell.basename(d)
        files = set([shell.basename(f) for f in shell.ls(d, config.submissionFileGlob)])
        expected = set(config.assignments)
        missing = expected - files
        superfluous = files - expected
        for m in missing:
            candidates = []
            for s in superfluous:
                if s.endswith(m) or len(superfluous) == 1:
                   candidates.append(s)
            if len(candidates) > 1:
                print(f'Cannot fix name of assignment {m} for {student} because there is more than one matching file')
            elif len(candidates) == 1:
                c = candidates[0]
                # Windows
                shell.run(['mv', '-i', shell.pjoin(d, c), shell.pjoin(d, m)])


def addComment(cfg):
    submissionDirs = collectSubmissionDirs(cfg)
    print(submissionDirs)
    for d in submissionDirs:
        p = shell.pjoin(d, cfg.commentsFile)
        verbose(f'Writing file {p}')
        writeFile(p, """In dieser Datei stehen allgemeine Kommentare zur Abgabe.

Die Bewertung finden Sie in der Datei POINTS.txt.

Möglicherweise enthalten die Quelldateien aufgaben-spezifische Kommentare. Diese sind mit TUTOR/TUTORIN oder
DOZENT/DOZENTIN gekennzeichnet.

=============================================================================================================

""")

def parseArgs():
    parser = argparse.ArgumentParser(description='Check student submissions')
    parser.add_argument('--verbose', help='Be more verbose', action='store_true')
    parser.add_argument('--baseDir', metavar='DIR', type=str, required=False,
                        help='Directory with tests for the assignment. Default: current directory')
    subparsers = parser.add_subparsers(help='Commands', dest='cmd')
    checkFilenames = subparsers.add_parser('checkFilenames', help='Check that all solutions are placed in the right files')
    fixFilenames = subparsers.add_parser('fixFilenames', help='Try to fix the names of the solution files')
    checkPlagiarism = subparsers.add_parser('checkPlagiarism', help='Run a check against plagiarism')
    checkPlagiarism.add_argument('--threshold', metavar='N', type=int, required=True,
                                 help='Similarity in percentage when two files are considered equal in the sense of plagiarism')
    checkPlagiarism.add_argument('--ignore', metavar='FILES', type=str, required=False,
                                 help='Ignore these assignment files when checking plagiarism')
    unzip = subparsers.add_parser('unzip', help='Unzip all files downloaded from moodle')
    addComment = subparsers.add_parser('addComment', help='Add a file COMMENTS.txt to all student directories')
    runTests = subparsers.add_parser('runTests', help='Run the tests, do interactive grading')
    runTests.add_argument('dirs', metavar='DIR', type=str, nargs='*',
                          help='The student directories to run the tests for.')
    runTests.add_argument('--assignments', help='Comma-separated list of assignments', type=str, metavar='LIST', dest='assignments')
    runTests.add_argument('--interactive', help='Run the tests interactively', action='store_true', dest='interactive')
    runTests.add_argument('--startAt', help='Start point (a submission directory)', metavar='DIR', dest='startAt')
    importCmd = subparsers.add_parser('import', help='Import a .csv file from moodle to produce an Excel spreadsheet for rating')
    importCmd.add_argument('file', metavar='CSV_FILE', type=str, help='A .csv file from moodle')
    prepareCmd = subparsers.add_parser('prepare', help='Shortcut for import+unzip+addComment')
    prepareCmd.add_argument('file', metavar='CSV_FILE', type=str, help='A .csv file from moodle')
    export = subparsers.add_parser('export',
                                   help='From rating.xlsx, generate a POINTS.txt file for each student and a single .csv file for uploading in moodle')
    return parser.parse_args()

def main():
    global VERBOSE
    args = parseArgs()
    if args.verbose:
        enableVerboseLogging()
    if args.baseDir:
        baseDir = args.baseDir
    else:
        baseDir = shell.pwd()
    config = mkConfig(baseDir)
    if args.cmd == 'checkFilenames':
        checkFilenames(config)
    elif args.cmd == 'checkPlagiarism':
        a = plagiarismCmd.PlagiarismArgs(args.threshold, args.ignore, VERBOSE)
        plagiarismCmd.checkPlagiarism(config, a)
    elif args.cmd == 'fixFilenames':
        fixFilenames(config)
    elif args.cmd == 'import':
        importArgs = importCmd.ImportArgs(args.file)
        importCmd.importCmd(config, importArgs)
    elif args.cmd == 'unzip':
        unzipCmd.unzip(config)
    elif args.cmd == 'addComment':
        addComment(config)
    elif args.cmd == 'prepare':
        importArgs = importCmd.ImportArgs(args.file)
        importCmd.importCmd(config, importArgs)
        unzipCmd.unzip(config)
        addComment(config)
    elif args.cmd == 'runTests':
        if args.assignments:
            assignments = args.assignments.split(',')
        else:
            assignments = []
        a = testCmd.TestArgs(args.dirs, assignments, args.interactive, stripSlashes(args.startAt))
        testCmd.runTests(config, a)
    elif args.cmd == 'export':
        exportCmd.export(config)
    elif not args.cmd:
        warn('No command given!')
    else:
        warn('Unknown command: ' + args.cmd)

if __name__ == '__main__':
    main()
