import unittest
import config
import utils

class ConfigTest(unittest.TestCase):
    def test_parse(self):
        cfg = config.mkConfig('test-data', {})
        d = '/Users/swehr/Teaching/WS2122/AdvancedProg-Praktikum/P04-real-world/'
        testDir = d + 'code/tutor/'
        a1 = cfg.assignments[0]
        self.assertEqual([d + 'stack.yaml', d + 'package.yaml', d + 'sample-dir'], a1.itemsToCopy)
        tests1 = a1.tests
        self.assertEqual([
            config.Test('1_a', testDir, None, testDir + 'TutorTests04_01_a.hs'),
            config.Test('1_b', testDir, None, testDir + 'TutorTests04_01_b.hs'),
        ], tests1)
        a2 = cfg.assignments[1]
        tests2 = a2.tests
        self.assertEqual([
            config.Test('2_TutorTests04_02_a', testDir, None, testDir + 'TutorTests04_02_a.hs'),
            config.Test('2_TutorTests04_02_b', testDir, None, testDir + 'TutorTests04_02_b.hs')
        ], tests2)
        a3 = cfg.assignments[2]
        self.assertEqual([
            config.Test('3', testDir, None, testDir + 'TutorTest_03.hs'),
        ], a3.tests)
        a4 = cfg.assignments[3]
        self.assertEqual([
            config.Test('4_pkg.ALL', 'subdir', 'pkg.*', None),
            config.Test('4_pkg2.ALL', 'subdir', 'pkg2.*', None)
        ], a4.tests)

    def test_expandVars(self):
        self.assertEqual('foo bar baz', config.expandVarsInStr('foo ${x} baz', {'x': 'bar'}))
        self.assertEqual('foo bar baz', config.expandVarsInStr('foo ${x-y} baz', {'x-y': 'bar'}))
        self.assertEqual('foo bar baz', config.expandVarsInStr('foo $x baz', {'x': 'bar'}))
        self.assertEqual({'k': [1, "two", "three"]},
            config.expandVars({'k': [1, "two", "$x"]}, {'x': 'three'}))

    def test_parse2(self):
        s = utils.readFile('test-data/check2.yml')
        cfg = config.mkConfigFromString('test-data', {}, s)
        t = cfg.assignments[0].tests[0]
        self.assertEqual(config.Test('2_a', 'sub/src/klausur/aufgabe_02/test_2A', '*', None), t)
