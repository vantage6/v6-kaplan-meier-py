from os import path
from codecs import open
from setuptools import setup, find_packages

# package description
cwd = path.abspath(path.dirname(__file__))
with open(path.join(cwd, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='vtg_km',
    version="1.0.0",
    description='vantage6 correlation matrix',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mdw-nl/v6-km-studyathon',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=[
        'vantage6-algorithm-tools==4.2.0','numpy','pandas'
    ]
)
