# check-assignments

A tool for checking programming assignments. Currently supports checking assignments
in Java, Python and Haskell.

# Prerequisites

## General

* Python 3.9 or 3.10: https://www.python.org
* PIP, the package installer for Python: https://pypi.org/project/pip/
* Python libraries:
  * pyyaml: `pip install pyyaml`
  * openpyxl: `pip install openpyxl` (only needed for the commands `import`, `prepare` and `export`)

## Language-specific

### Java

* gradle: https://gradle.org

### Python

* write-your-python-program: https://github.com/skogsbaer/write-your-python-program

# Installation

Copy the file `check-assignments` (Linux, Mac) or `check-assignments.bat`
to some place in the path. Then edit the copied file and adjust
the variables in the file to match the paths on your local machine.
Now you should be able to execute `check-assignments` in your shell.

# Usage

`check-assignments` has several commands. Simple invoke `check-assignments --help`
to get an overview. To see details for a command `CMD`, invoke
`check-assignments CMD --help`.

The directory layout for checking submissions for some assignments looks
like this:

```
check.yml         (configuration file)
build.gradle      (optional, only required for java)
tests/            (contains test files supplied by the teaching staff)
rating.xlsx       (optional)
STUDENT_1/
...
STUDENT_n/
```

`STUDENT_1` ... `STUDENT_n` contain the students' submissions, `rating.xlsx` is
a spreadsheet for recording credits for the individual assignments (optional).
If you download submission from moodle, then the `import` command can be
used to generate `rating.xlsx`

You must invoked all commands from within the top-level directory of the
submissions.

The workflow of checking the submissions is triggered by invoking
`check-assignments runTests --interactive`. The tool then iterates through
all submission and runs the tests for each assignment, pausing after
each exercise so that you can inspect the source code and records the credits
for the exercise.

# Configuration

The assignments are configured in the file `check.yml`. See
[test-data/submissions/check.yml](test-data/submissions/check.yml)
for an example.

## Variable expansion

In strings of yaml-values, you might refer to the value of a top-level defined variables `V`
as `${V}`. The special variables `${N}` and `${NN}` refer to the ID of an
assignment (unpadded and zero-padded).

## Top-level keys

* `test-dir`: directory for test files, default to `tests` inside the root directory.
* `assignments`: Under the `assignments` key each assignment is listed with its number. The keys for individual assignments are listed in the subsection
"assignment specific keys".

## Assignment specific keys

For each assignment, you have the following options available.

* `points`: the number of points for the assignment.
* `kind`: the programming language in which the solution is expected.
* `disable-tests`: disable the tests, only compile if appropriate for the
  language.

### Keys for `kind: "java"`

* `test-filter`: a package name with wildcards. The value of this key can be used
as `${testFilter}` in the `build.gradle` file.
* `java-simple`: `true` if java-simple be in the classpath.

### Keys for `kind: "python"`

* `main-file`: the main file the student is expected to submit
* `test-file`: file inside `tests` with tests provided by the teaching staff.

## Default Values

You can also place assignment-specific key-value pairs at the top-level.
The values than act as a default to the key.

## Checking Java code

Running tests for Java code are executed using gradle. Your top-level
directory must contain a `build.gradle` file. See
[test-data/submissions/build.gradle](test-data/submissions/build.gradle) for
an example. You can use the following properties (using the `${PROP_NAME}` notation)
in your `build.gradle` file:

* `testFilter`: for running tests in only certain packages. The value of
  this property is set via the `test-filter` key in `check.yml`.
* `studentDir`: directory of the students code
* `testDir`: directory of the test code

## Checking Python code

Python code is check via write-your-python-program
(WYPP, see https://github.com/skogsbaer/write-your-python-program)
You can supply your tests either via WYPP's check function
or you can write regular unittests. See
[test-data/submissions/tests/Test-01.py](test-data/submissions/tests/Test-01.py)
for an example.

Regular unittests should include the following code snippet at the end:

```python
if __name__ == '__wypp__':
    unittest.main()
```
