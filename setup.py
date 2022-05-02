from distutils.core import setup
from setuptools import find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='doodad',
    version='0.3.0dev',
    packages=find_packages(),
    include_package_data=True,
    install_requires=required,
    license='MIT License',
    long_description=open('README.md').read(),
)
