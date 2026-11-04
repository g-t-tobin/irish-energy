from setuptools import setup, find_packages

setup(
    name="lambda-deps",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "boto3==1.34.127",
        "requests==2.31.0",
        "urllib3==2.0.7",
        "loguru==0.7.2",
        "pandas==2.1.3",
        "pyarrow==15.0.0",
    ],
)