#!/usr/bin/env python
import unittest

def main():
    loader = unittest.TestLoader()
    tests = loader.discover(start_dir='.', pattern='*_test.py')
    test_runner = unittest.runner.TextTestRunner(verbosity=2)
    test_runner.run(tests)

if __name__ == '__main__':
    main()
