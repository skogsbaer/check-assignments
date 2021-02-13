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
                shell.run(['mv', '-i', shell.pjoin(d, c), shell.pjoin(d, m)])


def addComment(config):
    root_path = config.baseDir
    pattern = config.submissionFileGlob
    start = config.lineCommentStart()
    for root, dirs, files in os.walk(root_path):
        for filename in fnmatch.filter(files, pattern):
            file_path = os.path.join(root, filename)
            try:
                data = readFile(file_path)
                writeFile(file_path, f'{start}Anmerkungen (Dozent/Tutor*in):\n{start}-\n\n\n' + data)
            except Exception:
                pass

def parseArgs():
    parser = argparse.ArgumentParser(description='Check student submissions')
    parser.add_argument('--verbose', help='Be more verbose', action='store_true')
    parser.add_argument('--baseDir', metavar='DIR', type=str, required=False,
                        help='Directory with tests for the assignment. Default: current directory')
    parser.add_argument('--testDir', metavar='DIR', type=str, required=False,
                        help='Directory with tests for the assignment. Default: $BASE/tests')
    parser.add_argument('--assignments', metavar='FILENAMES', type=str, required=False,
                        help='List of file names (comma-separated) expected for solutions of assignments. ' +
                             f'Default: files in test directory (they must have the same extension).')
    parser.add_argument('--fileExt', metavar='EXT', type=str, required=False,
                        help='Filename extension for test cases and submissions. Per default: the unique extension ' +
                             'of all files in the test directory')
    subparsers = parser.add_subparsers(help='Commands', dest='cmd')
    checkFilenames = subparsers.add_parser('checkFilenames', help='check that all solutions are placed in the right files')
    fixFilenames = subparsers.add_parser('fixFilenames', help='try to file that filenames of solutions')
    checkPlagiarism = subparsers.add_parser('checkPlagiarism', help='run a check against plagiarism')
    checkPlagiarism.add_argument('--threshold', metavar='N', type=int, required=True,
                                 help='Similarity in percentage when two files are considered equal in the sense of plagiarism')
    checkPlagiarism.add_argument('--ignore', metavar='FILES', type=str, required=False,
                                 help='Ignore these assignment files when checking plagiarism')
    unzip = subparsers.add_parser('unzip', help='unzip all files')
    addComment = subparsers.add_parser('addComment', help='add comment to all submitted source code files')
    runTests = subparsers.add_parser('runTests', help='run the tests')
    runTests.add_argument('filesOrDirs', metavar='FILE_OR_DIR', type=str, nargs='*',
                          help='The student files or directories to run the tests for.')
    runTests.add_argument('--only-syntax', help='Only check syntax', action='store_true', dest='onlySyntax')
    runTests.add_argument('--interactive', help='Run the tests interactively', action='store_true', dest='interactive')
    runTests.add_argument('--startAt', help='Start point (a submission directory)', metavar='DIR', dest='startAt')
    runTests.add_argument('--cmd',
                          help='Custom test command, gets passed the submitted file and the corresponding test in the test directory',
                          metavar='FILE', dest='testCmd')
    importCmd = subparsers.add_parser('import', help='Import a .csv file to produce an Excel spreadsheet')
    importCmd.add_argument('--points', dest='points', metavar='POINTS', type=str, required=True,
                           help='A comma-separated list of points per assigment.')
    importCmd.add_argument('file', metavar='CSV_FILE', type=str,
                           help='A .csv file from moodle')
    export = subparsers.add_parser('export', help='Generate a POINTS.txt file for each student and a single .csv file for uploading in moodle')
    return parser.parse_args()

def main():
    global VERBOSE
    args = parseArgs()
    if args.verbose:
        enableVerboseLogging()
    assignments = None
    if args.assignments:
        assignments = [x.strip() for x in args.assignments.split(',') if x.strip()]
    if args.baseDir:
        baseDir = args.baseDir
    else:
        baseDir = shell.pwd()
    config = mkConfig(baseDir, fileExt=args.fileExt, assignments=assignments, testDir=args.testDir)
    if args.cmd == 'checkFilenames':
        checkFilenames(config)
    elif args.cmd == 'checkPlagiarism':
        a = plagiarismCmd.PlagiarismArgs(args.threshold, args.ignore, VERBOSE)
        plagiarismCmd.checkPlagiarism(config, a)
    elif args.cmd == 'fixFilenames':
        fixFilenames(config)
    elif args.cmd == 'unzip':
        unzipCmd.unzip(config)
    elif args.cmd == 'addComment':
        addComment(config)
    elif args.cmd == 'runTests':
        a = testCmd.TestArgs(args.filesOrDirs, args.onlySyntax, args.interactive, stripSlashes(args.startAt), args.testCmd)
        testCmd.runTests(config, a)
    elif args.cmd == 'export':
        exportCmd.export(config)
    elif args.cmd == 'import':
        try:
            maxPoints = [int(x.strip()) for x in args.points.split(',')]
        except ValueError:
            abort('Invalid value for option --points: ' + args.points)
        importArgs = importCmd.ImportArgs(args.file, maxPoints)
        importCmd.importCmd(config, importArgs)
    elif not args.cmd:
        warn('No command given!')
    else:
        warn('Unknown command: ' + args.cmd)

if __name__ == '__main__':
    main()
