"""Setup script for InfraMind CLI"""

from setuptools import setup, find_packages

with open("../README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="inframind-cli",
    version="0.1.0",
    author="InfraMind Team",
    author_email="hello@inframind.dev",
    description="CLI tool for InfraMind CI/CD optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/inframind",
    py_modules=["inframind"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "inframind=inframind:main",
        ],
    },
)
