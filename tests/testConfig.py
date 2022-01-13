import unittest
import config

class ConfigTest(unittest.TestCase):
    def test_parse(self):
        cfg = config.mkConfig('test-data', {})
        d = '/Users/swehr/Teaching/WS2122/AdvancedProg-Praktikum/P04-real-world/'
        self.assertEqual(d + 'code/tutor/', cfg.testDir)
        self.assertEqual([d + 'stack.yaml', d + 'package.yaml', d + 'sample-dir'],
            cfg.assignments[0].copyItems)
        print(cfg)

    def test_expandVars(self):
        self.assertEqual('foo bar baz', config.expandVarsInStr('foo ${x} baz', {'x': 'bar'}))
        self.assertEqual('foo bar baz', config.expandVarsInStr('foo $x baz', {'x': 'bar'}))
        self.assertEqual({'k': [1, "two", "three"]},
            config.expandVars({'k': [1, "two", "$x"]}, {'x': 'three'}))
