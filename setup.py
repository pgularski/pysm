import os
import codecs

from setuptools import find_packages, setup

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
    description='Versatile and flexible Python State Machine library',
    author='Piotr Gularski',
    author_email='piotr.gularski@gmail.com',
    license='MIT',
    long_description=read('README.rst'),
    long_description_content_type="text/x-rst",
    packages=find_packages(),
    package_data={'pysm': ['*.pyi', 'py.typed']},
    python_requires='>=3.7',
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: MicroPython',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Telecommunications Industry',
        'Natural Language :: English',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
    ],
    keywords='finite state machine automaton fsm hsm pda',
)
