import testPython
import unittest

unitOutput = """
F
======================================================================
FAIL: test_foo (__wypp__.TutorTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/var/folders/8r/25v12lxd02zdm7lpky3xcnh80000gn/T/tmpiic5dq2t/test-data/submissions/tests/Test-01.py", line 5, in test_foo
    self.assertEqual(41, foo())
AssertionError: 41 != 42

----------------------------------------------------------------------
Ran 5 test in 0.000s

FAILED (failures=1, errors=1, skipped=1)
"""

class TestPythonTest(unittest.TestCase):
    def test_parseUnitOutput(self):
        r = testPython.Result.parseResult('', unitOutput)
        self.assertEqual(testPython.Result(False, 4, 2), r)

