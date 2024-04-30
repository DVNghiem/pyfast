# -*- coding: utf-8 -*-
from setuptools import setup

from os import path

HERE = path.dirname(__file__)

long_description = 'resource'

version = '0.0.1'

with open(path.join(HERE, 'requirements.txt'), 'r') as f:
	install_requires = f.readlines()

setup(
	name='src',
	version=version,
	description="""resource""",
	long_description=long_description,
	long_description_content_type='text/markdown',
	license='MIT',
	classifiers=[
		'Intended Audience :: Developers',
		'Programming Language :: Python :: 3',
		'Operating System :: OS Independent',
	],
	install_requires=install_requires,
	packages=['src'],
	package_dir={'src': 'src'},
	python_requires='>=3.10',
	include_package_data=True,
	zip_safe=False,
)
