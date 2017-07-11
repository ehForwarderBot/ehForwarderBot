from setuptools import setup

__version__ = ""
exec(open('ehforwarderbot/__version__.py').read())

setup(
    name='ehforwarderbot',
    packages=['ehforwarderbot'],
    version=__version__,
    description='An extensible message tunneling chat bot framework.',
    author='Eana Hufwe',
    author_email='ilove@1a23.com',
    url='https://github.com/blueset/ehforwarderbot',
    license='GPL v3',
    download_url='',
    keywords=['', ' '],
    classifiers=[
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Utilities"
    ],
    install_requires=[
        "PyYaml"
    ]
)
