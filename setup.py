from codecs import open
from os import path

from setuptools import setup, find_packages

setup(
    name='crbtree',
    version='0.0.1',

    packages=find_packages(exclude=['test']),

    setup_requires=[
        "cffi>=1.4.0",
    ],
    install_requires=[
        "cffi>=1.4.0",
    ],

    cffi_modules=["rbtree_build.py:FFI_BUILDER"],
)
