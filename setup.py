from setuptools import setup, find_packages
from os import path

__version__ = "0.1.0"

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pymiscutils",
    version=__version__,
    description="Provides a wide range of useful classes and functions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matthewgdv/miscutils",
    license="MIT",
    classifiers=[
      "Development Status :: 3 - Alpha",
      "Intended Audience :: Developers",
      "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "colorama",
        "cryptography",
        "cursor",
        "dill",
        "django",
        "maybe-else",
        "pathmagic",
        "readchar",
        "pysubtypes",
        "pyinstrument"
    ],
    author="Matt GdV",
    author_email="matthewgdv@gmail.com"
)
