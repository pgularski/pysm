import os

from setuptools import setup, find_packages, Command
with open(os.path.join('pysm', 'VERSION')) as version_file:
    __version__ = version_file.read().strip()

setup(
    name='pysm',
    version=__version__,
    url='https://github.com/pgularski/pysm',
    description='Python State Machine',
    author='Piotr Gularski',
    author_email='piotr.gularski@gmail.com',
    license='MIT',
    packages=find_packages(),
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
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
)
