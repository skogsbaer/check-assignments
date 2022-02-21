import shell
import argparse
import exportCmd
import plagiarismCmd
import testCmd
import importCmd
import unzipCmd
import filenamesCmd
import jplagCmd
import fixEncodingCmd
import gradeCmd
import collectCmd
from ownLogging import *
from utils import *
from config import *

def addComment(cfg):
    submissionDirs = collectSubmissionDirs(cfg)
    print(submissionDirs)
    for d in submissionDirs:
        p = shell.pjoin(d, cfg.commentsFile)
        verbose(f'Writing file {p}')
        writeFile(p, """In dieser Datei stehen allgemeine Kommentare zur Abgabe.

Die Bewertung finden Sie in der Datei POINTS.txt.

Falls für Ihre Abgabe automatisch Tests ausgeführt wurden, finden Sie die
Ausgabe der Tests für die i-te Aufgabe in der Datei OUTPUT_i.txt
bzw. OUTPUT_student_i.txt (für Ihre eigenen Tests).

Möglicherweise enthalten die Quelldateien aufgaben-spezifische Kommentare.
Diese sind mit TUTOR/TUTORIN oder DOZENT/DOZENTIN gekennzeichnet, so dass
Sie bequem danach suchen können.

=============================================================================================================

""")

def parseArgs():
    parser = argparse.ArgumentParser(description='Check student submissions')
    parser.add_argument('--verbose', help='Be more verbose', action='store_true')
    parser.add_argument('--baseDir', metavar='DIR', type=str, required=False,
                        help='Directory with tests for the assignment. Default: current directory')
    parser.add_argument('--wypp', metavar='DIR', type=str, required=False,
                        help='Installation directory for write-your-python-program')
    parser.add_argument('--gradle', metavar='FILE', type=str, required=False,
                        help='Gradle executable')
    subparsers = parser.add_subparsers(help='Commands', dest='cmd')
    checkFilenames = subparsers.add_parser('checkFilenames', help='Check that all solutions are placed in the right files')
    fixFilenames = subparsers.add_parser('fixFilenames', help='Try to fix the names of the solution files')
    checkPlagiarism = subparsers.add_parser('checkPlagiarism', help='Run a check against plagiarism')
    checkPlagiarism.add_argument('--threshold', metavar='N', type=int, required=True,
                                 help='Similarity in percentage when two files are considered equal in the sense of plagiarism')
    checkPlagiarism.add_argument('--ignore', metavar='FILES', type=str, required=False,
                                 help='Ignore these assignment files when checking plagiarism')
    jplag = subparsers.add_parser('jplag', help='Detect plagiarism via jplag')
    jplag.add_argument('--mode', metavar='M', type=str, required=True,
                       help='Either "merged" (checks all files at once) or "separate" (checks each file individually)')
    unzip = subparsers.add_parser('unzip', help='Unzip all files downloaded from moodle')
    addComment = subparsers.add_parser('addComment', help='Add a file COMMENTS.txt to all student directories')
    runTests = subparsers.add_parser('runTests', help='Run the tests, do interactive grading')
    runTests.add_argument('dirs', metavar='DIR', type=str, nargs='*',
                          help='The student directories to run the tests for.')
    runTests.add_argument('--assignments', help='Comma-separated list of assignments', type=str, metavar='LIST', dest='assignments')
    runTests.add_argument('--interactive', nargs='?', const='assignment',
                         type=str, choices=['assignment', 'student'], dest='interactive',
                         help='Run the tests interactively, stop after each student|assignment where assignment is the default.', )
    runTests.add_argument('--startAt', help='Start point (a submission directory)', metavar='DIR', dest='startAt')
    runTests.add_argument('--sanityCheck', help='Only perform sanity checks on submission, do not run tests',
                          action='store_true', default=False)
    grade = subparsers.add_parser('grade', help='Grading')
    grade.add_argument('dirs', metavar='DIR', type=str, nargs='*',
                       help='The student directories to run the tests for.')
    grade.add_argument('--assignments', help='Comma-separated list of assignments', type=str, metavar='LIST', dest='assignments')
    grade.add_argument('--startAt', help='Start point (a submission directory)', metavar='DIR', dest='startAt')
    importCmd = subparsers.add_parser('import', help='Import a .csv file from moodle to produce an Excel spreadsheet for rating')
    importCmd.add_argument('file', metavar='CSV_FILE', type=str, help='A .csv file from moodle')
    prepareCmd = subparsers.add_parser('prepare', help='Shortcut for import+unzip+addComment')
    prepareCmd.add_argument('file', metavar='CSV_FILE', type=str, help='A .csv file from moodle')
    export = subparsers.add_parser('export',
                                   help='From rating.xlsx, generate a POINTS.txt file for each student and a single .csv file for uploading in moodle')
    fixEnc = subparsers.add_parser('fixEncoding', help='Fix encoding of source files.')
    collect = subparsers.add_parser('collect', help='Colllect credits for assignment and store in spreadsheet')
    collect.add_argument('file', metavar='EXCEL_FILE', type=str, help='The spreadsheet where credits should be stored')
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
    if args.cmd is None:
        print('Welcome to check-assignments.')
        print('You did not specify any command.')
        print('Please use the --help flag to see which commands are available.')
        return
    configDict = {
        'gradle': args.gradle,
        'wypp': args.wypp
    }
    config = mkConfig(baseDir, configDict)
    if args.cmd == 'checkFilenames':
        filenamesCmd.checkFilenames(config)
    elif args.cmd == 'checkPlagiarism':
        a = plagiarismCmd.PlagiarismArgs(args.threshold, args.ignore, VERBOSE)
        plagiarismCmd.checkPlagiarism(config, a)
    elif args.cmd == 'fixFilenames':
        filenamesCmd.fixFilenames(config)
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
        a = testCmd.TestArgs(args.dirs,
            assignments,
            args.interactive,
            stripSlashes(args.startAt),
            args.sanityCheck)
        testCmd.runTests(config, a)
    elif args.cmd == 'grade':
        if args.assignments:
            assignments = args.assignments.split(',')
        else:
            assignments = []
        a = gradeCmd.GradeArgs(args.dirs, assignments, stripSlashes(args.startAt))
        gradeCmd.grade(config, a)
    elif args.cmd == 'export':
        exportCmd.export(config)
    elif args.cmd == 'jplag':
        a = jplagCmd.JplagArgs(args.mode)
        jplagCmd.jplag(config, a)
    elif args.cmd == 'fixEncoding':
        fixEncodingCmd.fixEncoding(config)
    elif args.cmd == 'collect':
        collectCmd.collect(config, args.file)
    else:
        warn('Unknown command: ' + args.cmd)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Exiting ...')
