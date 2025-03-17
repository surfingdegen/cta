#!/usr/bin/env python3
"""
Setup script for the Crypto Trading Agent package.
"""

from setuptools import setup, find_packages
import os

# Read the contents of README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Read the requirements
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = f.read().splitlines()

# Get version from src/__init__.py
with open(os.path.join('src', '__init__.py'), 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.split('=')[1].strip().strip("'").strip('"')
            break
    else:
        version = '0.1.0'

setup(
    name='crypto-trading-agent',
    version=version,
    description='AI-powered cryptocurrency trading agent',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Crypto Trading Agent Contributors',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/crypto-trading-agent',
    packages=find_packages(),
    package_dir={'crypto_trading_agent': 'src'},
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'crypto-trading-agent=src.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
    python_requires='>=3.8',
    keywords='cryptocurrency, trading, blockchain, sentiment-analysis, technical-analysis',
)
