import codecs
from setuptools import setup

# Get the long description from the relevant file
with codecs.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='xiami-downloader',
    version="0.3.1",
    description='Python script for download preview music from xiami.com.',
    long_description=long_description,

    url='https://github.com/timothyqiu/xiami-downloader',

    author='Timothy Qiu',

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2',
    ],

    py_modules=['xiami', 'xiami_dl', 'xiami_util'],

    entry_points={
        'console_scripts': [
            'xiami=xiami:main',
        ],
    },
)
