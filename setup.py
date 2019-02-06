from setuptools import setup, find_packages
from typing import List
from pathlib import Path


def parse_requirements(filename: str) -> List[str]:
    """Return requirements from requirements file."""
    # Ref: https://stackoverflow.com/a/42033122/
    requirements = (Path(__file__).parent / filename).read_text().strip().split('\n')
    requirements = [r.strip() for r in requirements]
    requirements = [r for r in sorted(requirements) if r and not r.startswith('#')]
    return requirements


setup(name="SparqlTransformer",
      version="1.6.2",
      packages=find_packages(),
      scripts=['sparqlTransformer.py'],

      install_requires=parse_requirements('requirements.txt'),

      # metadata to display on PyPI
      author="Pasquale Lisena",
      author_email="pasquale.lisena@eurecom.fr",
      description="Write your SPARQL query directly in the JSON-LD you would like to have in output",
      license="Apache 2.0",
      keywords="sparql json json-ld semantic",
      url="https://github.com/D2KLab/py-sparql-transformer",  # project home page, if any
      project_urls={
          "Bug Tracker": "https://github.com/D2KLab/py-sparql-transformer/issues",
          "Documentation": "https://github.com/D2KLab/py-sparql-transformer",
          "Source Code": "https://github.com/D2KLab/py-sparql-transformer",
      })
