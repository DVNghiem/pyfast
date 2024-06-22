# -*- coding: utf-8 -*-
from setuptools import setup

from os import path
from Cython.Build import cythonize

HERE = path.dirname(__file__)

long_description = 'Atom resource'

version = '0.0.1'

with open(path.join(HERE, 'requirements.txt'), 'r') as f:
	install_requires = f.readlines()

setup(
	name='src',
	version=version,
	description="""Atom resource""",
	long_description=long_description,
	long_description_content_type='text/markdown',
	url='https://google.com',
	author='Van Nghiem',
	author_email='vannghiem848@gmail.com',
	license='MIT',
	classifiers=[
		'Intended Audience :: Developers',
		'Programming Language :: Python :: 3',
		'Operating System :: OS Independent',
	],
	install_requires=install_requires,
	packages=['src'],
	package_dir={'src': 'build/src'},
	python_requires='>=3.10',
	include_package_data=True,
	package_data={'': ['*.so', '*/*.so', '*/**/*.so']},
	zip_safe=False,
	ext_modules=cythonize(['src/*.py', 'src/**/*.py']),
)
