#!/usr/bin/env python

from pip.req import parse_requirements

install_reqs = parse_requirements("requirements.txt", session=False)

reqs = [str(ir.req) for ir in install_reqs]

setup(name='pgoapi',
      version='1.0',
      url='https://github.com/tejado/pgoapi',
      packages=['pgoapi'],
      install_requires=reqs)
