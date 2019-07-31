Py SPARQL Transformer
=====================

Write your SPARQL query directly in the JSON-LD you would like to have in output.

> Looking for the [JavaScript Version](https://github.com/D2KLab/sparql-transformer)?


## News

- It is now possible to set a different **merging anchor** instead of `id`/`@id` using the `$anchor` modifier.

**Table of Contents**

- [Motivation](https://github.com/D2KLab/sparql-transformer/blob/master/motivation.md)
- [Query in JSON](https://github.com/D2KLab/sparql-transformer#query-in-json)
- [How to use](#how-to-use)
- [Credits](#credits)


## How to use

Install by pip.

```bash
pip install SPARQLTransformer
```
Use in your JS application (node or browser).

```python
from SPARQLTransformer import sparqlTransformer

out = sparqlTransformer(query, options)
```

The first parameter (`query`) is the query in the JSON format. The JSON can be:
- an already parsed (or defined real time) `dict`,
- the local path of a JSON file (that will then be read and parsed).

The `options` parameter is optional, and can define the following:

| OPTION | DEFAULT | NOTE |
| --- | --- | --- |
|context | <http://schema.org/> | The value in `@context`. It overwrites the one in the query.|
| sparqlFunction | `None` | A function receiving in input the transformed query in SPARQL, returning a Promise. If not specified, the module performs the query on its own<sup id="a1">[1](#f1)</sup> against the specified endpoint.  |
| endpoint | <http://dbpedia.org/sparql> | Used only if `sparqlFunction` is not specified. |
| debug | `False` | Enter in debug mode. This allow to print in console the generated SPARQL query. |


See [`tests.py`](./test.py) for further examples.


## Credits

If you use this module for your research work, please cite:

> Pasquale Lisena, Albert Meroño-Peñuela, Tobias Kuhn and Raphaël Troncy. Easy Web API Development with SPARQL Transformer. In 18th International Semantic Web Conference (ISWC), Auckland, New Zealand, October 26-30, 2019.

[BIB file](https://github.com/D2KLab/sparql-transformer/blob/master/bib/lisena2019easyweb.bib)


> Pasquale Lisena and Raphaël Troncy. Transforming the JSON Output of SPARQL Queries for Linked Data Clients. In WWW'18 Companion: The 2018 Web Conference Companion, April 23–27, 2018, Lyon, France.
<https://doi.org/10.1145/3184558.3188739>

[BIB file](https://github.com/D2KLab/sparql-transformer/blob/master/bib/lisena2018sparqltransformer.bib)


<!--
python setup.py sdist
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
twine upload dist/*
-->
