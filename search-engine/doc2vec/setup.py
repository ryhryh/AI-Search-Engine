import setuptools
pkgs = [
    "tensorflow==2.3.1",
    "tensorflow-text==2.3.0",
    "tensorflow-transform==0.25.0",
    "tensorflow-hub==0.9.0",
    #"tfx-bsl==0.25.0",
]

setuptools.setup(
    name='dataflow',
    version='0.0',
    install_requires=pkgs,
    packages=setuptools.find_packages(),
)