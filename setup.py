import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 6):
    raise Exception("Python 3.6 or higher is required. Your version is %s." % sys.version)

long_description = open('README.rst').read()

__version__ = ""
exec(open('ehforwarderbot/__version__.py').read())

setup(
    name='ehforwarderbot',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    version=__version__,
    description='An extensible message tunneling chat bot framework.',
    long_description=long_description,
    author='Eana Hufwe',
    author_email='ilove@1a23.com',
    url='https://github.com/blueset/ehforwarderbot',
    license='GPLv3',
    python_requires='>=3.6',
    include_package_data=True,
    keywords=['EFB', 'EH Forwarder Bot', 'Chat tunneling', 'IM', 'messaging'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Utilities"
    ],
    install_requires=[
        "PyYaml"
    ],
    entry_points={
        "console_scripts": ['ehforwarderbot = ehforwarderbot.__main__:main']
    }
)
