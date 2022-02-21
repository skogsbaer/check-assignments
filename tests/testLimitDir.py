import unittest
import shell
import utils

class LimitDirTest(unittest.TestCase):
    def test_limit(self):
        with shell.tempDir() as d:
            shell.mkdir(d+"/A/K/X", createParents=True)
            shell.mkdir(d+"/A/K/Y", createParents=True)
            shell.mkdir(d+"/A/L", createParents=True)
            shell.mkdir(d+"/B")
            shell.mkdir(d+"/C")
            shell.touch(d+"/A/L/x.txt")
            shell.touch(d+"/A/K/x.txt")
            shell.touch(d+"/A/K/X/x.txt")
            shell.touch(d+"/A/K/Y/x.txt")
            shell.touch(d+"/B/x.txt")
            shell.touch(d+"/C/x.txt")
            def action(d):
                self.assertTrue(shell.isFile(d+"/A/K/x.txt"))
                self.assertTrue(shell.isFile(d+"/A/K/X/x.txt"))
                self.assertTrue(shell.isFile(d+"/A/K/Y/x.txt"))
                self.assertTrue(shell.isFile(d+"/C/x.txt"))
                self.assertFalse(shell.isFile(d+"/B/x.txt"))
                self.assertFalse(shell.isFile(d+"/A/L/x.txt"))
                self.assertFalse(shell.isDir(d+"/B"))
                self.assertFalse(shell.isDir(d+"/A/L"))
            utils.withLimitedDir(d, ['./C', 'A/K/'], action)
