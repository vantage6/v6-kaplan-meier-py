from os import path
from codecs import open
from setuptools import setup, find_packages

# package description
cwd = path.abspath(path.dirname(__file__))
with open(path.join(cwd, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="v6-kaplan-meier-py",
    version="1.0.0",
    description="vantage6 Kaplan-Meier curve",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vantage6/v6-kaplan-meier-py",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "vantage6-algorithm-tools",
        "numpy",
        "pandas",
        "rpy2",
        "ohdsi-common",
        "ohdsi-database-connector",
        "ohdsi-sqlrender",
    ],
    package_data={"v6-kaplan-meier-py": ["sql/*.sql"]},
)
