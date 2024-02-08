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
import removeEmptyCmd
import praktomatTestCmd
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
    fixFilenames.add_argument('--moveUp', help='Move contents if a single directory one level up', action='store_true', default=False)
    checkPlagiarism = subparsers.add_parser('checkPlagiarism', help='Run a check against plagiarism')
    checkPlagiarism.add_argument('--threshold', metavar='N', type=int, required=True,
                                 help='Similarity in percentage when two files are considered equal in the sense of plagiarism')
    checkPlagiarism.add_argument('--ignore', metavar='FILES', type=str, required=False,
                                 help='Ignore these assignment files when checking plagiarism')
    jplag = subparsers.add_parser('jplag', help='Detect plagiarism via jplag')
    jplag.add_argument('--mode', metavar='M', type=str, default='separate',
                       help='Either "merged" (checks all files at once) or "separate" (checks each file individually, the default, ' + \
                           'requires a main-file for the assignments to be checked)')
    jplag.add_argument('--minScore', metavar='S', type=int, default=95,
                       help='Minimum score for which similarities are reported on the commandline (0-100, default 95)')
    jplag.add_argument('--printDiff',  action='store_true', default=False,
                       help='Print diff if score is 100%%')
    unzip = subparsers.add_parser('unzip', help='Unzip all files downloaded from moodle')
    addComment = subparsers.add_parser('addComment', help='Add a file COMMENTS.txt to all student directories')
    runTests = subparsers.add_parser('runTests',
                                     help='DEPRECATED, better use --runPraktomatTests. ' +
                                          'Run the tests, do interactive grading')
    runTests.add_argument('dirs', metavar='DIR', type=str, nargs='*',
                          help='The student directories to run the tests for.')
    runTests.add_argument('--assignments', help='Comma-separated list of assignments', type=str, metavar='LIST', dest='assignments')
    runTests.add_argument('--interactive', nargs='?', const='assignment',
                         type=str, choices=['assignment', 'student'], dest='interactive',
                         help='Run the tests interactively, stop after each student|assignment where assignment is the default.', )
    runTests.add_argument('--startAt', help='Start point (a submission directory)', metavar='DIR', dest='startAt')
    runTests.add_argument('--sanityCheck', help='Only perform sanity checks on submission, do not run tests',
                          action='store_true', default=False)
    runTests.add_argument('--openSpreadsheet',
                          help='Automatically open the grading spreadsheet (only with "--interactive assignment")',
                          action='store_true', default=False)
    runPrTests = subparsers.add_parser('runPraktomatTests', help='Run the tests with praktomat-checkers')
    runPrTests.add_argument('dirs', metavar='DIR', type=str, nargs='*',
                          help='The student directories to run the tests for.')
    runPrTests.add_argument('--startAt', help='Start point (a submission directory)', metavar='DIR', dest='startAt')
    runPrTests.add_argument('--assignments', help='Comma-separated list of assignments', type=str, metavar='LIST', dest='assignments')
    runPrTests.add_argument('--praktomat', metavar='ARGUMENTS',
                            help='Pass arguments directly to praktomat-checker command. Arguments are splitted on whitespace')
    grade = subparsers.add_parser('grade', help='Grading for exams')
    grade.add_argument('dirs', metavar='DIR', type=str, nargs='*',
                       help='The student directories to run the tests for.')
    grade.add_argument('--assignments', help='Comma-separated list of assignments', type=str, metavar='LIST', dest='assignments')
    grade.add_argument('--startAt', help='Start point (a submission directory)', metavar='DIR', dest='startAt')
    rmEmpty = subparsers.add_parser('removeEmpty', help='Remove empty submission directories')
    rmEmpty.add_argument('--dry',  action='store_true', default=False,
                         help='Dry run, do not actually remove unchanged directories')
    rmEmpty.add_argument('templateDir', metavar='TEMPLATE_DIR', type=str,
                         help='The template directory. Directories unchanged wrt this directory are removed.')
    rmEmpty.add_argument('dirs', metavar='STUDENT_DIR', type=str, nargs='*',
                         help='The student directories to cleanup.')
    rmEmpty.add_argument('--uidCol', help='Title of the uid column, default: Login',
                         metavar='COL', default='Login')
    rmEmpty.add_argument('--contentCol', help='Title of the colum whose content must be non-empty, default: A1',
                         metavar='COL', default='A1')
    rmEmpty.add_argument('--sheet', help='.xlsx file with ratings', metavar='FILE', required=True)
    importCmd = subparsers.add_parser('import', help='Import a .csv file from moodle to produce an Excel spreadsheet for rating')
    importCmd.add_argument('file', metavar='CSV_FILE', type=str, help='A .csv file from moodle')
    prepareCmd = subparsers.add_parser('prepare', help='Shortcut for import+unzip+addComment')
    prepareCmd.add_argument('file', metavar='CSV_FILE', type=str, help='A .csv file from moodle')
    export = subparsers.add_parser('export',
                                   help='From rating.xlsx, generate a POINTS.txt file for each student and a single .csv file for uploading in moodle')
    fixEnc = subparsers.add_parser('fixEncoding', help='Fix encoding of source files.')
    collect = subparsers.add_parser('collect', help='Colllect credits for assignment and store in spreadsheet')
    collect.add_argument('--file', metavar='EXCEL_FILE', type=str, help='The spreadsheet where credits should be stored')
    collect.add_argument('--startAt', help='Start point (a submission directory)', metavar='DIR', dest='startAt')
    collect.add_argument('--sheetName', default='Ergebnis', help='Name of the sheet in the spreadsheet')
    collect.add_argument('--completeness', help='Only check if all assignments have been examined for all students',
                         action='store_true', default=False)
    collect.add_argument('--eklausurenMoodle', help='Submission come from Eklausuren Moodle (requires a special ID fix)',
                         action='store_true', default=False)
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
        fixArgs = filenamesCmd.FixFilenamesArgs(args.moveUp)
        filenamesCmd.fixFilenames(config, fixArgs)
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
            args.sanityCheck,
            args.openSpreadsheet)
        testCmd.runTests(config, a)
    elif args.cmd == 'runPraktomatTests':
        if args.assignments:
            assignments = args.assignments.split(',')
        else:
            print(f'The {args.cmd} command requires an explicit list of assignments')
            return
        a = praktomatTestCmd.PrTestArgs(args.dirs, stripSlashes(args.startAt), assignments,
                                        args.praktomat.split())
        praktomatTestCmd.runTests(config, a)
    elif args.cmd == 'grade':
        if args.assignments:
            assignments = args.assignments.split(',')
        else:
            assignments = []
        a = gradeCmd.GradeArgs(args.dirs, assignments, stripSlashes(args.startAt))
        gradeCmd.grade(config, a)
    elif args.cmd == 'removeEmpty':
        a = removeEmptyCmd.RemoveEmptyArgs(args.sheet, args.uidCol, args.contentCol,
                                           args.templateDir, args.dirs, args.dry)
        removeEmptyCmd.removeEmpty(config, a)
    elif args.cmd == 'export':
        exportCmd.export(config)
    elif args.cmd == 'jplag':
        a = jplagCmd.JplagArgs(args.mode, args.minScore, args.printDiff)
        jplagCmd.jplag(config, a)
    elif args.cmd == 'fixEncoding':
        fixEncodingCmd.fixEncoding(config)
    elif args.cmd == 'collect':
        if not args.completeness and not args.file:
            print(f'Option --file required')
        a = collectCmd.CollectArgs(args.startAt, args.file, args.sheetName,
                                   args.completeness, args.eklausurenMoodle)
        collectCmd.collect(config, a)
    else:
        warn('Unknown command: ' + args.cmd)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Exiting ...')
