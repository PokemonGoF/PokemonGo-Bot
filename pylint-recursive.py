#! /usr/bin/env python
'''
Author: gregorynicholas (github), modified by Jacob Henderson (jacohend, github)
Module that runs pylint on all python scripts found in a directory tree..
''' 

import os
#import re
import sys

passed = 0
failed = 0
errors = list()

IGNORED_FILES = ["lcd.py"]

def check(module):
  global passed, failed
  '''
  apply pylint to the file specified if it is a *.py file
  '''
  module_name = module.rsplit('/', 1)[1]
  if module[-3:] == ".py" and module_name not in IGNORED_FILES:
    print "CHECKING ", module
    pout = os.popen('pylint %s'% module, 'r')
    for line in pout:
      if "Your code has been rated at" in line:
        print "PASSED pylint inspection: " + line
        passed += 1
        return True
      if "-error" in line:
        print "FAILED pylint inspection: " + line
        failed += 1
        errors.append("FILE: " + module)
        errors.append("FAILED pylint inspection: " + line)
        return False
  
if __name__ == "__main__":
  try:
    print sys.argv   
    BASE_DIRECTORY = sys.argv[1]
  except IndexError:
    print "no directory specified, defaulting to current working directory"
    BASE_DIRECTORY = os.getcwd()

  print "looking for *.py scripts in subdirectories of ", BASE_DIRECTORY

  for root, dirs, files in os.walk(BASE_DIRECTORY):
    for name in files:
      filepath = os.path.join(root, name)
      check(filepath)

  print "Passed: " + str(passed) + " Failed: " + str(failed)
  print "\n"
  print "Showing errors:"
  if failed > 0:
    for err in errors:
      print err

    sys.exit("Pylint failed with errors")
