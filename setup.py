from distutils.core import setup
from setuptools import find_packages

setup(
    name='doodad',
    version='0.3.0dev',
    packages=find_packages(),
    # scripts=['doodad/darchive/makeself.sh'],
    # package_data={'': ['doodad/darchive/makeself.sh']},
    include_package_data=True,
    license='MIT License',
    long_description=open('README.md').read(),
)
