#!/usr/bin/env python
from setuptools import setup
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="tap-geosource",
    version="0.1.1",
    description="Singer.io tap for extracting geo data",
    author="Jules Huisman",
    author_email="jules.huisman@quantile.nl",
    url="https://github.com/JulesHuisman/tap-geosource",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_geosource"],
    long_description=README,
    long_description_content_type="text/markdown",
    install_requires=[
        "singer-python==5.12.1",
        "pathlib==1.0.1",
        "GDAL==2.4.0"
    ],
    entry_points="""
    [console_scripts]
    tap-geosource=tap_geosource:main
    """,
    packages=["tap_geosource"],
    include_package_data=True
)
