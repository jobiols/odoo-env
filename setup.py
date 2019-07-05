# -*- coding: utf-8 -*-

import setuptools
from odoo_env import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='odoo-env',
    version=__version__,
    author='Jorge E. Obiols',
    description='An environment to manage Docker for Odoo',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/jobiols/odoo-env',
    author_email='jorge.obiols@gmail.com',
    entry_points={
        'console_scripts': [
            'oe=odoo_env.oe:main',
            'sd=odoo_env.sd:main'
        ],
    },
    install_requires=[],
    data_files=[('', ['odoo_env/data/nginx.conf'])],
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Testing :: Unit",
        "Topic :: System :: Software Distribution",
    ],
    keywords="odoo docker environment",
)
