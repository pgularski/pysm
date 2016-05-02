#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages, Command


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


setup(
    name='pysm',
    version='0.1',
    url='https://github.com/pgularski/pysm',
    description='Python State Machine',
    author='Piotr Gularski',
    author_email='piotr.gularski@gmail.com',
    license='MIT',
    packages=find_packages(),
    zip_safe=True,

    tests_require=['pytest', 'pytest-cov', 'mock'],
    cmdclass={'test': PyTest},
)
