import os
import json
import string
import unittest
from unittest.mock import patch
from simplejson import dumps
from SPARQLTransformer import sparqlTransformer, pre_process
import SPARQLTransformer

OUTPUT = './examples/json_transformed/'
JSONLD_QUERIES = './examples/json_queries/'
SPARQL_OUTPUT = './examples/sparql_output/'
SPARQL_QUERIES = './examples/sparql_queries/'

opt = {
    'debug': True
}


def mock(filename):
    with open(os.path.join(SPARQL_OUTPUT, filename)) as data:
        obj = json.load(data)

    def f(self):
        class x:
            @staticmethod
            def convert():
                return obj

        return x

    return f


def load(filename):
    with open(os.path.join(JSONLD_QUERIES, filename)) as data:
        q = json.load(data)
    with open(os.path.join(OUTPUT, filename)) as data:
        expected = json.load(data)
    with open(os.path.join(SPARQL_QUERIES, filename.replace('.json', '.rq'))) as data:
        rq = data.read().strip()

    return q, expected, rq


def get_sparql_query(q):
    query, proto, opt = pre_process(q, {'debug': False})
    return query


def cleans(s):
    return s.translate({ord(c): None for c in string.whitespace})


class TestStringMethods(unittest.TestCase):
    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('city.list.json'))
    def test_proto(self):
        q, expected, rq = load('city.list.json')

        outSparql = get_sparql_query(q)
        self.assertEqual(cleans(outSparql), cleans(rq))

        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('city.list.ld.json'))
    def test_jsonld(self):
        q, expected, rq = load('city.list.ld.json')
        outSparql = get_sparql_query(q)
        self.assertEqual(cleans(outSparql), cleans(rq))

        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('city.region.list.ld.json'))
    def test_nested(self):
        q, expected, rq = load('city.region.list.ld.json')
        outSparql = get_sparql_query(q)
        self.assertEqual(cleans(outSparql), cleans(rq))

        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('band.json'))
    def test_anchor(self):
        q, expected, rq = load('band.json')
        outSparql = get_sparql_query(q)
        self.assertEqual(cleans(outSparql), cleans(rq))

        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('band_reversed.json'))
    def test_reversed(self):
        q, expected, rq = load('band_reversed.json')
        outSparql = get_sparql_query(q)
        self.assertEqual(cleans(outSparql), cleans(rq))

        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('issue_10_duplicate_vars.json'))
    def test_reversed(self):
        q, expected, rq = load('issue_10_duplicate_vars.json')
        outSparql = get_sparql_query(q)
        self.assertEqual(cleans(outSparql), cleans(rq))

        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    @patch.object(SPARQLTransformer.SPARQLWrapper, 'query', mock('aggregates.json'))
    def test_aggregates(self):
        q, expected, rq = load('aggregates.json')
        outSparql = get_sparql_query(q)
        self.assertEqual(cleans(outSparql), cleans(rq))

        out = sparqlTransformer(q, opt)
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))


if __name__ == '__main__':
    unittest.main()
