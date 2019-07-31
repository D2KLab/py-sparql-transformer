from setuptools import setup
from os import path


with open('requirements.txt') as fp:
    requirements = fp.read()

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name="SPARQLTransformer",
      version="1.7.0",
      install_requires=requirements,
      data_files=[('txt', ['requirements.txt'])],
      py_modules=["SPARQLTransformer"],

      # metadata to display on PyPI
      author="Pasquale Lisena",
      author_email="pasquale.lisena@eurecom.fr",
      description="Write your SPARQL query directly in the JSON-LD you would like to have in output",
      long_description=long_description,
      long_description_content_type='text/markdown',
      license="Apache 2.0",
      keywords="sparql json json-ld semantic",
      url="https://github.com/D2KLab/py-sparql-transformer",  # project home page, if any
      project_urls={
          "Bug Tracker": "https://github.com/D2KLab/py-sparql-transformer/issues",
          "Documentation": "https://github.com/D2KLab/py-sparql-transformer",
          "Source Code": "https://github.com/D2KLab/py-sparql-transformer",
      })
