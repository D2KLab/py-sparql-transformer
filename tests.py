import unittest
import json
from simplejson import dumps
import os
from SPARQLTransformer import sparqlTransformer

OUTPUT = "./examples/json_transformed/"
JSONLD_QUERIES = "./examples/json_queries/"


class TestStringMethods(unittest.TestCase):

    def test_proto(self):
        q, expected = load('city.list.json')
        out = sparqlTransformer(q, {
            'debug': True
        })
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    def test_jsonld(self):
        q, expected = load('city.list.ld.json')
        out = sparqlTransformer(q, {
            'debug': True
        })
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))

    def test_nested(self):
        q, expected = load('city.region.list.ld.json')
        out = sparqlTransformer(q, {
            'debug': True
        })
        # with open('a.json', 'w') as o:
        #     json.dump(out, o)

        self.assertEqual(dumps(out), dumps(expected))


def load(filename):
    with open(os.path.join(JSONLD_QUERIES, filename)) as data:
        q = json.load(data)
    with open(os.path.join(OUTPUT, filename)) as data:
        expected = json.load(data)

    return q, expected


if __name__ == '__main__':
    unittest.main()
