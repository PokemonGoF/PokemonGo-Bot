#!/usr/bin/env python
import unittest

loader = unittest.TestLoader()
tests = loader.discover(start_dir='.', pattern='*_test.py')
testRunner = unittest.runner.TextTestRunner(verbosity=2)
testRunner.run(tests)
