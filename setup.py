import os
from setuptools import setup, find_packages

f = open(os.path.join(os.path.dirname(__file__), 'README.md'))
readme = f.read()
f.close()

setup(
    name='xiami-downloader',
    version="0.2.0.1",
    description='Python script for download preview music from xiami.com.',
    long_description=readme,
    author='Timothy Qiu',
    url='https://github.com/timothyqiu/xiami-downloader',
    py_modules=['xiami', 'xiami_dl'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
)
