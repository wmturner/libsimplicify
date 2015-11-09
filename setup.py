# Copyright (C) Simplicify, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by William Michael Turner <williammichaelturner@gmail.com>, 2015

from setuptools import setup

setup(name='simplicify',
      version='0.1',
      description='Complete end-to-end data center service discovery',
      url='http://github.com/storborg/funniest',
      author='Flying Circus',
      author_email='williammichaelturner@gmail.com',
      license='All Rights Reserved',
      packages=['simplicify'],
      install_requires=[
          'boto',
          'dnspython',
          'python-etcd',
      ],
      zip_safe=False)
