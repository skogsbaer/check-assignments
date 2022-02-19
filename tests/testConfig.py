import unittest
import config

class ConfigTest(unittest.TestCase):
    def test_parse(self):
        cfg = config.mkConfig('test-data', {})
        d = '/Users/swehr/Teaching/WS2122/AdvancedProg-Praktikum/P04-real-world/'
        testDir = d + 'code/tutor/'
        self.assertEqual(d + 'code/tutor/', cfg.testDir)
        a1 = cfg.assignments[0]
        self.assertEqual([d + 'stack.yaml', d + 'package.yaml', d + 'sample-dir'], a1.itemsToCopy)
        tests1 = a1.getTestFiles(cfg.testDir)
        self.assertEqual([
            ('a', testDir + 'TutorTests04_01_a.hs'), ('b', testDir + 'TutorTests04_01_b.hs'),
        ], tests1)
        a2 = cfg.assignments[1]
        tests2 = a2.getTestFiles(cfg.testDir)
        self.assertEqual(5, len(tests2))
        self.assertEqual( ('TutorTests04_02_a.hs', testDir + 'TutorTests04_02_a.hs'),
            tests2[0])
        print(cfg)

    def test_expandVars(self):
        self.assertEqual('foo bar baz', config.expandVarsInStr('foo ${x} baz', {'x': 'bar'}))
        self.assertEqual('foo bar baz', config.expandVarsInStr('foo $x baz', {'x': 'bar'}))
        self.assertEqual({'k': [1, "two", "three"]},
            config.expandVars({'k': [1, "two", "$x"]}, {'x': 'three'}))
