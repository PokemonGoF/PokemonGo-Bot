#! /usr/bin/env python
'''
Check whether a json file is loadable
''' 

import json
import sys

passed = 0
failed = 0
errors = list()

def check(filename):
  global passed, failed

  print "CHECKING ", filename

  f = open(filename).read()
  try:
      _ = json.loads(f)
      print "PASSED: ", filename
      passed += 1
      return True
  except ValueError as e:
      failed += 1
      print "FAILED: ", filename
      errors.append("FILE: " + filename)
      errors.append(e)
      return False
 
  return False
  
if __name__ == "__main__":
  for filename in sys.argv[1:]:
    check(filename)

  print "Passed: " + str(passed) + " Failed: " + str(failed)
  print "\n"
  print "Showing errors:"
  if failed > 0:
    for err in errors:
      print err

    sys.exit("JSON check Failed with errors")
