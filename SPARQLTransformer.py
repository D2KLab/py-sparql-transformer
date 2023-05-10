import logging
import pprint
import os
import re
import json
import copy
from SPARQLWrapper import SPARQLWrapper, JSON
from simplejson import dumps

INDENT = '          '

DEFAULT_OPTIONS = {
    'context': 'http://schema.org/',
    'endpoint': 'http://dbpedia.org/sparql',
    'langTag': 'show'
}

KEY_VOCABULARIES = {
    'JSONLD': {
        'id': '@id',
        'lang': '@language',
        'value': '@value'
    },
    'PROTO': {
        'id': 'id',
        'lang': 'language',
        'value': 'value'
    }
}

LANG_REGEX = re.compile(r"^lang(?::(.+))?")
AGGREGATES = ['sample', 'count', 'sum', 'min', 'max', 'avg']

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)
logger = logging.getLogger('sparql_transformer')


def pre_process(json_query, options=None):
    _input = json_query.copy()
    opt = DEFAULT_OPTIONS.copy()
    if '@context' in _input:
        opt['context'] = _input['@context']
    if options is not None:
        opt.update(options)

    if 'debug' in opt and opt['debug']:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.NOTSET)

    logger.debug('OPTIONS:')
    if logger.getEffectiveLevel() == logging.DEBUG:
        pprint.pprint(opt)

    if isinstance(_input, str):
        if os.path.isfile(_input):
            with open(_input) as data:
                _input = json.load(data)
        else:
            return logger.error('Wrong input. I require a path to a JSON file')
    elif not isinstance(_input, dict):
        return logger.error('Input format not valid')
    else:
        _input = copy.deepcopy(_input)

    #   I save the info about hideLang before it is destroyed
    if '$langTag' in _input:
        opt['langTag'] = _input['$langTag']

    proto, query = _jsonld2query(_input)

    is_json_ld = '@graph' in _input
    voc = KEY_VOCABULARIES['JSONLD' if is_json_ld else 'PROTO']
    opt['voc'] = voc
    opt['is_json_ld'] = is_json_ld

    if '$limitMode' in json_query and '$limit' in json_query:
        opt['limit'] = json_query['$limit']
        opt['offset'] = json_query.get('$offset', 0)

    return query, proto, opt


def post_process(sparql_res, proto, opt):
    is_json_ld = opt['is_json_ld']

    bindings = sparql_res['results']['bindings']
    # apply the proto
    instances = list(map(lambda b: _sparql2proto(b, proto, opt), bindings))
    # merge lines with the same id
    content = []
    anchor = instances[0]['$anchor'] if (len(instances) > 0 and '$anchor' in instances[0]) else None
    if not anchor:
        content = instances
    else:
        for inst in instances:
            _id = inst[anchor]
            # search if we have already the same id
            match = [x for x in content if x[anchor] == _id]
            if not match:  # it is a new one
                content.append(inst)
            else:  # otherwise modify previous one
                _merge_obj(match[0], inst)

    # remove anchor tag
    for i in content:
        clean_recursively(i)

    if 'limit' in opt:
        content = content[opt['offset']: opt['offset'] + opt['limit']]

    if is_json_ld:
        return {
            '@context': opt['context'],
            '@graph': content
        }
    return content


def sparqlTransformer(_input, options=None):
    query, proto, opt = pre_process(_input, options)
    sparql_fun = opt['sparqlFunction'] if 'sparqlFunction' in opt else _default_sparql(opt['endpoint'])
    sparql_res = sparql_fun(query)

    logger.debug(sparql_res)

    return post_process(sparql_res, proto, opt)


def _jsonld2query(_input):
    """Read the input and extract the query and the prototype"""
    proto = _input['@graph'] if '@graph' in _input else _input['proto']
    if isinstance(proto, list):
        proto = proto[0]

    # get all props starting with '$'
    modifiers = {}
    for k in list(_input):
        if not k.startswith('$'):
            continue
        modifiers[k] = _input.pop(k, None)

    _vars = []
    filters = _as_array(modifiers.get('$filter'))
    wheres = _as_array(modifiers.get('$where'))
    main_lang = modifiers.get('$lang')

    values_normalized = normalize_values(modifiers.get('$values', None))
    mpk_fun, _temp = _manage_proto_key(proto, _vars, filters, wheres, main_lang, values=values_normalized)
    for i, key in enumerate(list(proto)):
        mpk_fun(key, i)

    wheres = [w.strip() for w in wheres]
    wheres = [w for w in wheres if w]

    _from = ('FROM <%s>' % modifiers['$from']) if '$from' in modifiers else ''
    limit = ('LIMIT %d' % modifiers['$limit']) if (
            '$limit' in modifiers and modifiers.get('$limitMode') != 'library') else ''
    offset = 'OFFSET ' + str(modifiers['$offset']) if (
            '$offset' in modifiers and modifiers.get('$limitMode') != 'library') else ''
    distinct = '' if ('$distinct' in modifiers and modifiers['$distinct'] == 'false') else 'DISTINCT'
    prefixes = _parse_prefixes(modifiers['$prefixes']) if '$prefixes' in modifiers else []
    values = parse_values(values_normalized) if '$values' in modifiers else []
    orderby = 'ORDER BY ' + ' '.join(_as_array(modifiers['$orderby'])) if '$orderby' in modifiers else ''
    groupby = 'GROUP BY ' + ' '.join(_as_array(modifiers['$groupby'])) if '$groupby' in modifiers else ''
    having = 'HAVING(%s)' % ' && '.join(_as_array(modifiers['$having'])) if '$having' in modifiers else ''

    filterz = list(map(lambda f: 'FILTER(%s)' % f, filters))
    query = '\n'.join(prefixes) + """
        SELECT %s %s
        %s
        WHERE {
          %s
          %s
          %s
        }
        %s
        %s
        %s
        %s
        %s
    """ % (distinct, ' '.join(_vars), _from, ('\n' + INDENT).join(values), ('.\n' + INDENT).join(wheres),
           ('\n' + INDENT).join(filterz),
           groupby, having, orderby, limit, offset)

    query = re.sub(r"\n+", "\n", query)
    query = re.sub(r"\n\s+\n", "\n", query)
    query = re.sub(r"\.+", ".", query)
    logger.info(query)
    return proto, query


def normalize_values(values):
    """
    Transform all key of a object to a sparqlVariable
    adding the '?' if required
    """
    if values is None:
        return {}
    out = dict()
    for key, value in values.items():
        out[_sparql_var(key)] = value
    return out


def _default_sparql(endpoint):
    sparql = SPARQLWrapper(endpoint)
    sparql.setReturnFormat(JSON)

    def exec_query(q):
        sparql.setQuery(q)
        return sparql.query().convert()

    return exec_query


def _parse_prefixes(prefixes):
    return list(map(lambda key: 'PREFIX %s: <%s>' % (key, prefixes[key]), prefixes.keys()))


def parse_values(values):
    res = []
    for p in list(values):
        __v = []

        for v in _as_array(values[p]):
            if type(v) == str:
                if v.startswith('http'):
                    __v.append(f'<{v}>')
                elif ':' in v:
                    __v.append(v)
                elif re.match(r'^.+@[a-z]{2,3}(_[A-Z]{2})?$', v):
                    vv, langtag = v.split('@')
                    __v.append(f'"{vv}"@{langtag}')
                else:
                    __v.append(f'"{v}"')
            else:
                __v.append(v)
        res.append('VALUES %s {%s}' % (_sparql_var(p), ' '.join(map(str, __v))))
    return res


def _sparql2proto(line, proto, options):
    """Apply the prototype to a single line of query results"""
    instance = copy.deepcopy(proto)

    fii_fun = _fit_in(instance, line, options)
    for key in list(instance):
        fii_fun(key)
    return instance


def _fit_in(instance, line, options):
    """Apply the result of SPARQL to a single property of the proto instance"""

    def fit(k):
        variable = instance[k]

        # if value is an obj
        if isinstance(variable, dict):
            obj_as_list = variable.get('$list', variable.get('$asList', False))
            fii_fun = _fit_in(variable, line, options)
            for key in list(variable):
                fii_fun(key)
            if _is_empty_obj(variable):
                instance.pop(k)
            elif obj_as_list:
                instance[k] = [instance[k]]
            return

        if isinstance(variable, list):
            fii_fun = _fit_in(variable, line, options)
            for i in range(len(variable)):
                fii_fun(i)
            if all(item is None for item in variable):
                instance.pop(k)
            return

        if not isinstance(variable, str):
            return

        if not variable.startswith('?'):
            return

        variable = variable[1:]
        accept = None
        langTag = options['langTag']
        asList = '$list' in variable or '$asList' in variable
        variable = re.sub(r'\$(asL|l)ist', '', variable)

        if "$accept:" in variable:
            temp = variable.split('$accept:')
            variable = temp[0]
            accept = temp[1]
        if "$langTag:" in variable:
            temp = variable.split('$langTag:')
            variable = temp[0]
            langTag = temp[1]

        # variable not in result, delete from
        if variable not in line:
            if isinstance(instance, list):
                instance[k] = None
            else:
                instance.pop(k)
        else:
            opt = options.copy()
            opt['accept'] = accept
            opt['langTag'] = langTag
            opt['list'] = asList
            instance[k] = _to_jsonld_value(line[variable], opt)

            if instance[k] is None:
                instance.pop(k)

        return instance

    return fit


def _is_empty_obj(target):
    for key in list(target):
        if key not in ['@type', '$anchor']:
            return False
    return True


XSD = 'http://www.w3.org/2001/XMLSchema#'


def xsd(resource):
    return XSD + resource


XSD_INT_TYPES = [xsd('integer'), xsd('nonPositiveInteger'), xsd('negativeInteger'),
                 xsd('nonNegativeInteger'), xsd('xs,positiveInteger'),
                 xsd('long'), xsd('int'), xsd('short'), xsd('byte'),
                 xsd('unsignedLong'), xsd('unsignedInt'), xsd('unsignedShort'), xsd('unsignedByte')]

XSD_FLOAT_TYPES = [xsd('decimal'), xsd('float'), xsd('double')]

known_types = {
    'int': [int],
    'float': [float],
    'number': [int, float],
    'str': [str],
    'string': [str],
    'boolean': [bool],
    'bool': [bool]
}


def _to_jsonld_value(_input, options):
    """Prepare the output managing languages and datatypes"""
    value = _input['value']
    if 'datatype' in _input:
        if _input['datatype'] == xsd('boolean'):
            value = value not in ['false', '0', 0, 'False', False]
        elif _input['datatype'] in XSD_INT_TYPES:
            value = int(value)
        elif _input['datatype'] in XSD_FLOAT_TYPES:
            value = value.replace('INF', 'inf')
            value = float(value)

    # I can't accept 0 if I want a string
    if 'accept' in options and options.get('accept') is not None:
        if type(value) not in known_types[options.get('accept')]:
            return None

    # nothing more to do for other types
    if not isinstance(value, str):
        return [value] if options['list'] else value

    # if here, it is a string or a date, that are not parsed
    if 'xml:lang' in _input and options['langTag'] != 'hide':
        lang = _input['xml:lang']

        voc = options['voc']
        if lang:
            return {
                voc['lang']: lang,
                voc['value']: value
            }
    return [value] if options['list'] else value


def _merge_obj(base, addition):
    """Merge base and addition, by defining/adding in an array the values in addition to the base object.
    Return the base object merged."""
    for k in list(addition):
        if k == '$anchor':
            continue

        a = addition[k]
        if k not in base:
            base[k] = a
            continue

        b = base[k]

        anchor = None
        if isinstance(a, dict) and '$anchor' in a:
            anchor = a['$anchor']

        # if a is array, I take its value
        if isinstance(a, list):
            a = a[0]

        if isinstance(b, list):
            if anchor:
                same_ids = [x for x in b if anchor in x and a[anchor] == x[anchor]]
                if len(same_ids) > 0:
                    _merge_obj(same_ids[0], a)
                    continue

            if not any([_deepequals(x, a) for x in b]):
                b.append(a)
            continue

        if _deepequals(a, b):
            continue

        if anchor and anchor in b and a[anchor] == b[anchor]:  # same ids
            _merge_obj(b, a)
        else:
            base[k] = [b, a]

    return base


def _compute_root_id(proto, prefix):
    k = None

    # check if an anchor is set
    for key, value in proto.items():
        if type(value) == str and '$anchor' in value:
            k = key
            break

    # otherwise, check if one of the default anchors is there
    if k is None:
        for key, value in KEY_VOCABULARIES.items():
            if KEY_VOCABULARIES[key]['id'] in proto:
                k = KEY_VOCABULARIES[key]['id']
                break

    if k is None:
        return None, None

    txt = proto[k]
    modifiers = txt.split('$')
    _rootId = modifiers.pop(0)

    required = True if 'required' in modifiers else (not not _rootId)
    _var = [s for s in modifiers if s.startswith('var:')]
    if len(_var) > 0:
        _rootId = _sparql_var(_var[0].split(':')[1])

    if not _rootId:  # generate it
        _rootId = "?" + prefix + "r"
        proto[k] += '$var:' + _rootId

    proto['$anchor'] = k
    proto['$list'] = '$list' in proto[k] or '$asList' in proto[k]
    return _rootId, required


def _sparql_var(_input):
    """Add the "?" if absent"""
    return _input if _input.startswith('?') else '?' + _input


def _manage_proto_key(proto, vars=[], filters=[], wheres=[], main_lang=None, prefix="v", prev_root=None, values={}):
    """Parse a single key in prototype"""
    _rootId, _blockRequired = _compute_root_id(proto, prefix)
    _rootId = _rootId or prev_root or '?id'

    def inner(k, i=''):
        if k in ['$anchor', '$list', '$asList']:
            return
        v = proto[k]
        if isinstance(v, dict):
            wheres_internal = []
            mpk_fun, bk_req = _manage_proto_key(v, vars, filters, wheres_internal,
                                                main_lang, prefix + str(i), _rootId, values)

            for i, k in enumerate(list(v)):
                mpk_fun(k, i)

            wheres_internal = '.\n'.join(wheres_internal)
            wheres.append(wheres_internal if bk_req else 'OPTIONAL { %s }' % wheres_internal)
            return

        if not isinstance(v, str):
            return

        is_dollar = v.startswith('$')
        if not is_dollar and not v.startswith('?'):
            return
        if is_dollar:
            v = v[1:]

        options = []
        if '$' in v:
            options = v.split('$')
            v = options.pop(0)

        original_id = ('?' + prefix + str(i)) if is_dollar else v
        id = original_id

        _var = [s for s in options if s.startswith('var:')]
        if len(_var) > 0:
            id = _sparql_var(_var[0].split(':')[1])
            if not id.startswith('?'):
                id = '?' + id

        _accept = [s for s in options if s.startswith('accept')]
        _bestlang = [s for s in options if s.startswith('bestlang')]
        _langTag = [s for s in options if s.startswith('langTag')]

        aggregate = [a for a in AGGREGATES if a in options]
        aggr_what = id if is_dollar else original_id
        if len(aggregate) > 0 and len(_var) == 0:
            id = original_id if is_dollar else f"?{aggregate[0]}_{original_id.replace('?', '')}"

        required = 'required' in options or k in ['id', '@id'] or id in values or (len(aggregate) > 0 and is_dollar)
        # if it is an id or I specified a value, this property can not be optional

        proto[k] = id

        _var = id
        if 'sample' in options:
            _var = '(SAMPLE(%s) AS %s)' % (id, id)

        if len(aggregate) > 0:
            distinct_txt = 'DISTINCT ' if 'distinct' in options else ''
            _var = f"({aggregate[0].upper()}({distinct_txt}{aggr_what}) AS {id})"

        if len(_bestlang) > 0:
            _bestlang = _bestlang[0]
            proto[k] = id + '$accept:string'
            lng = _bestlang.split(':')[1] if ':' in _bestlang else main_lang
            if lng is None:
                raise AttributeError('bestlang require a language declared inline or in the root')

            _var = '(sql:BEST_LANGMATCH(%s, "%s", "en") AS %s)' % (id, lng, id)
        elif len(_accept) > 0:
            proto[k] = id + '$' + _accept[0]

        if len(_langTag) > 0:
            proto[k] = proto[k] + '$' + _langTag[0]

        if ('list' in options or 'asList' in options) and id != _rootId:
            proto[k] += '$list'

        if _var not in vars:
            vars.append(_var)

        # lang filters are managed here, so that they stay within the OPTIONAL
        lang_filter = ''
        _lang = [LANG_REGEX.match(s).group(1) for s in options if LANG_REGEX.match(s)]

        if len(_lang) > 0:
            _lang = _lang[0]
            if _lang is None and main_lang is not None:
                _lang = re.split('[;,]', main_lang)[0]
            if _lang:
                _lang = _lang.strip()
                if id in values and type(values[id]) == str:
                    values[id] += '@' + _lang
                else:
                    lang_filter = ".\n%sFILTER(lang(%s) = '%s')" % (INDENT, id, _lang)

        reverse = 'reverse' in options
        if is_dollar:
            use_prev_root = (id == _rootId) or ('prevRoot' in options and prev_root is not None)

            subject = prev_root if use_prev_root else _rootId

            subj = id if reverse else subject
            obj = subject if reverse else id

            q = ' '.join([subj, v, obj])
            q += lang_filter
            wheres.append(q if required else '%sOPTIONAL { %s }' % (INDENT, q))

    return inner, _blockRequired


def _prepare_groupby(array=None):
    if array is None:
        return ''

    for s in array:
        if 'desc' in s:
            s.pop('desc')

    return _prepare_orderby(array, 'GROUP BY')


# Remove development properties
def clean_recursively(instance):
    if isinstance(instance, list):
        for i in instance:
            clean_recursively(i)
        return

    if isinstance(instance, dict):
        instance.pop('$anchor', None)  # remove $anchor
        instance.pop('$list', None)  # remove $anchor
        instance.pop('$asList', None)  # remove $anchor
        for k, v in instance.items():
            clean_recursively(v)


def _prepare_orderby(array=None, keyword='ORDER BY'):
    if array is None or len(array) == 0:
        return ''

    sorted_array = sorted(array, key=lambda x: x.priority)
    mapped_array = list(map(lambda s: 'DESC(%s)' % s['variable'] if 'desc' in s else s.variable, sorted_array))
    return keyword + ' ' + ' '.join(mapped_array)


def _parse_order(str, variable):
    _ord = {'variable': variable, 'priority': 0}
    s = str.split(':')

    s.pop()  # first one is always 'order'

    if 'desc' in s:
        _ord['desc'] = True
        s.pop(s.indexOf('desc'))

    if len(s) > 0:
        _ord.priority = int(s[0])

    return _ord


def _as_array(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def _deepequals(a, b):
    return a == b or dumps(a) == dumps(b)
