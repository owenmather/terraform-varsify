from setuptools import setup

setup(
    name='tvarsify',
    version='0.4',
    packages=['tvarsify'],
    url='',
    license='BSD 2-clause',
    author='Owen.Mather',
    description='Takes an existing terraform file or folder and converts all hardcoded values to variables & tfvars',
    include_package_data=True,
    entry_points={
        'console_scripts': ['tvarsify=tvarsify.tvarsify:tvarsify_cli'],
    },
)
