from setuptools import setup

from xiami_downloader import __version__


with open('README.md') as f:
    long_description = f.read()


url = 'https://github.com/timothyqiu/xiami-downloader'
download_url = '{0}/archive/{1}.tar.gz'.format(url, __version__)

setup(
    name='xiami_downloader',
    version=__version__,
    packages=['xiami_downloader'],
    entry_points={
        'console_scripts': [
            'xiami = xiami_downloader.cli:main',
        ],
    },
    license='MIT',
    description='Python script for download preview music from xiami.com.',
    long_description=long_description,
    author='Timothy Qiu',
    author_email='timothyqiu32@gmail.com',
    url=url,
    download_url=download_url,
    keywords=['xiami'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2',
    ],
)
