#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-geosource",
    version="0.1.0",
    description="Singer.io tap for extracting geo data",
    author="Jules Huisman",
    url="http://singer.io",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_geosource"],
    install_requires=[
        "singer-python==5.11.0",
        "pathlib==1.0.1"
    ],
    entry_points="""
    [console_scripts]
    tap-geosource=tap_geosource:main
    """,
    packages=["tap_geosource"]
)
