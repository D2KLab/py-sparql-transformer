import os
import json
import unittest
from unittest.mock import patch
from simplejson import dumps
from SPARQLTransformer import sparqlTransformer
import SPARQLTransformer

OUTPUT = "./examples/json_transformed/"
JSONLD_QUERIES = "./examples/json_queries/"
SPARQL_OUTPUT = "./examples/sparql_output/"

opt = {
    'debug': False
}


def mock(filename):
    with open(os.path.join(SPARQL_OUTPUT, filename)) as data:
        obj = json.load(data)

    def f(self):
        class x:
            def convert():
                return obj
        return x

    return f


def load(filename):
    with open(os.path.join(JSONLD_QUERIES, filename)) as data:
        q = json.load(data)
    with open(os.path.join(OUTPUT, filename)) as data:
        expected = json.load(data)

    return q, expected


class TestStringMethods(unittest.TestCase):
    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('city.list.json'))
    def test_proto(self):
        q, expected = load('city.list.json')

        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('city.list.ld.json'))
    def test_jsonld(self):
        q, expected = load('city.list.ld.json')
        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('city.region.list.ld.json'))
    def test_nested(self):
        q, expected = load('city.region.list.ld.json')
        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('band.json'))
    def test_anchor(self):
        q, expected = load('band.json')
        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))


if __name__ == '__main__':
    unittest.main()
