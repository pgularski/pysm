import codecs
import os
from setuptools import setup, find_packages, Command

HERE = os.path.abspath(os.path.dirname(__file__))

# Get __version__
exec(open('pysm/version.py').read())


def read(*parts):
    # Build an absolute path from *parts* and and return the contents of the
    # resulting file.  Assume UTF-8 encoding.
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


setup(
    name='pysm',
    version=__version__,
    url='https://github.com/pgularski/pysm',
    description='Python State Machine',
    author='Piotr Gularski',
    author_email='piotr.gularski@gmail.com',
    license='MIT',
    long_description=read('README.rst'),
    packages=find_packages(),
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Telecommunications Industry',
        'Natural Language :: English',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov', 'mock'],
    keywords='finite state machine automaton fsm hsm pda',
)
