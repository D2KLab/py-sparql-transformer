Py SPARQL Transformer
=====================

Write your SPARQL query directly in the JSON-LD you would like to have in output.
Python version of [SPARQL Transformer for JavaScript](https://github.com/D2KLab/sparql-transformer).

**Table of Contents**

- [Motivation](https://github.com/D2KLab/sparql-transformer#motivation)
- [Query in JSON](https://github.com/D2KLab/sparql-transformer#query-in-json)
- [How to use](#how-to-use)
- [Credits](#credits)


## How to use

Install by pip.

```bash
pip install sparqlTransformer
```
Use in your JS application (node or browser).

```python
from SparqlTransformer import sparqlTransformer

out = sparqlTransformer(query, options)
```

The first parameter (`query`) is the query in the JSON-LD format. The JSON-LD can be:
- an already parsed JS object (or defined real time),
- **ONLY if running in NodeJS**, the local path of a JSON file (that will then be read and parsed).

The `options` parameter is optional, and can define the following:

| OPTION | DEFAULT | NOTE |
| --- | --- | --- |
|context | http://schema.org/ | The value in `@context`. It overwrites the one in the query.|
| sparqlFunction | `None` | A function receiving in input the transformed query in SPARQL, returning a Promise. If not specified, the module performs the query on its own<sup id="a1">[1](#f1)</sup> against the specified endpoint.  |
| endpoint | http://dbpedia.org/sparql | Used only if `sparqlFunction` is not specified. |
| debug | `False` | Enter in debug mode. This allow to print in console the generated SPARQL query. |


See [`test.js`](./test.js) for further examples.


## Credits

If you use this module for your research work, please cite:

> Pasquale Lisena and Raphaël Troncy. Transforming the JSON Output of SPARQL Queries for Linked Data Clients. In WWW'18 Companion: The 2018 Web Conference Companion, April 23–27, 2018, Lyon, France.
https://doi.org/10.1145/3184558.3188739

[BIB file](https://github.com/D2KLab/sparql-transformer/blob/master/lisena2018sparqltransformer.bib)

---

<b id="f1">1</b>: Using [virtuoso-sparql-client](https://github.com/crs4/virtuoso-sparql-client).
