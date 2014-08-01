#-------------------------------------------------------------------------------
# Name:        editor
# Purpose:     Schema.org Editor
#
# Author:      Jeremy Nelson
#
# Created:     2014/09/07
# Copyright:   (c) Jeremy Nelson 2014
# Licence:     MIT
#-------------------------------------------------------------------------------
import datetime
import hashlib
import json
import random
import rdflib
import urllib

from flask import abort, Flask, g, jsonify, redirect, render_template, request
from flask import url_for

from string import Template

editor = Flask(__name__)

# fedora_base = 'http://172.25.1.108:8080/rest/'
fedora_base = 'http://localhost:8080/rest/schema/'
fcrepo = rdflib.Namespace('http://fedora.info/definitions/v4/repository#')
literal_set = set(['Text', 'Number', 'Date'])
schema_json = json.load(open('schema_org.json'))
schema_ns = rdflib.Namespace('http://schema.org/')


def create_entity(entity_id):
    entity_url = urllib.parse.urljoin(fedora_base, entity_id)
    print(entity_url)
    create_request = urllib.request.Request(
        entity_url,
        method='PUT')
    response = urllib.request.urlopen(create_request)
    return entity_url

def entity_exists(entity_id):
    entity_uri = urllib.parse.urljoin(fedora_base, entity_id)
    try:
        urllib.request.urlopen(entity_uri)
        return True
    except urllib.error.HTTPError:
        return False

def replace_entity_property(entity_id,
                            property_name,
                            old_value,
                            value):
##    if len(old_value) < 1:
##        return update_entity_property(entity_id, property_name, value)
    if not entity_id.startswith("http"):
        entity_uri = urllib.parse.urljoin(fedora_base, entity_id)
    else:
        entity_uri = entity_id
    if len(literal_set.intersection(
        ['properties'][property_name]['ranges'])) < 1 or\
        not 'ranges' in ['properties'][property_name]:
        sparql_template = Template("""PREFIX schema: <http://schema.org/>
        DELETE {
         <$entity> $prop_name <$old_value>
        } INSERT {
         <$entity> $prop_name <$new_value>
        } WHERE {
        }""")
    else:
        sparql_template = Template("""PREFIX schema: <http://schema.org/>
        DELETE {
         <$entity> $prop_name "$old_value"
        } INSERT {
         <$entity> $prop_name "$new_value"
        } WHERE {
        }""")
    sparql = sparql_template.substitute(
        entity=entity_uri,
        prop_name="schema:{}".format(property_name),
        old_value=old_value,
        new_value=value)
    update_request = urllib.request.Request(
        entity_uri,
        data=sparql.encode(),
        method='PATCH',
        headers={'Content-Type': 'application/sparql-update'})
    response = urllib.request.urlopen(update_request)
    if response.code < 400:
        return True
    return False


def update_entity_property(entity_id,
                           property_name,
                           value):
    """Method updates the Entity's property in Fedora4

    Args:
        entity_id(string): Unique ID of Fedora object
        property_name(string): Name of schema.org property
        value: Value of the schema.org property

    Returns:
        boolean: True if successful changed in Fedora, False otherwise
    """
    if not entity_id.startswith("http"):
        entity_uri = urllib.parse.urljoin(fedora_base, entity_id)
    else:
        entity_uri = entity_id
    if not entity_exists(entity_id):
        create_entity(entity_id)
    print(entity_uri)
    ranges_set = set(schema_json['properties'][property_name]['ranges'])
    if len(literal_set.intersection(ranges_set)) > 0:
        sparql_template = Template("""PREFIX schema: <http://schema.org/>
    INSERT DATA {
        <$entity> $prop_name "$prop_value"
    }""")
    else:
        sparql_template = Template("""PREFIX schema: <http://schema.org/>
    INSERT DATA {
        <$entity> $prop_name <$prop_value>
    }""")
    sparql = sparql_template.substitute(
        entity=entity_uri,
        prop_name="schema:{}".format(property_name),
        prop_value=value)
    update_request = urllib.request.Request(
        entity_uri,
        data=sparql.encode(),
        method='PATCH',
        headers={'Content-Type': 'application/sparql-update'})
    response = urllib.request.urlopen(update_request)
    if response.code < 400:
        return True
    return False

def retrieve_entity(entity_url):
    try:
        urllib.request.urlopen(entity_url)
    except urllib.error.HTTPError:
        abort(404)
    entity_graph = rdflib.Graph().parse(entity_url)
    entity_json = json.loads(entity_graph.serialize(format='json-ld').decode())
    return json.dumps(entity_json)

@editor.route("/list/<entity_type>")
def get_entities(entity_type):
    type_url = "{}{}".format(fedora_base,
                             entity_type)
    entities_graph = rdflib.Graph().parse(type_url)
    options = []
    for obj in entities_graph.objects(
        subject=rdflib.URIRef(type_url),
        predicate=fcrepo.hasChild):
            child = rdflib.Graph().parse(str(obj))
            label = child.value(subject=obj,
                                predicate=rdflib.RDFS.label)
            if label is None:
                schema_name = child.value(subject=obj,
                                          predicate=schema_ns.name)
                if schema_name is None:
                    options.append({'name': str(obj),
                                    'value': str(obj)})
                else:
                    options.append({'name': str(schema_name),
                                    'value': str(obj)})
            else:
                options.append({'name': str(label),
                                'value': str(obj)})
    return json.dumps(options)

@editor.route("/id")
def get_entity_from_url():
    url = request.args.get('url')
    return retrieve_entity(url)


@editor.route("/id/schema/<entity_type>/<entity_id>")
def get_entity_workspace(entity_type, entity_id):
    """


    """
    entity_url = '/'.join([fedora_base,
                           entity_type,
                           entity_id])
    return retrieve_entity(entity_url)



@editor.route("/id/<entity_type>/<entity_id>")
def get_entity(entity_type, entity_id):
    return retrieve_entity('/'.join([
        fedora_base,
        entity_type,
        entity_id]))




@editor.route("/id/new/<entity_type>")
def new_id(entity_type):
    random_str = "{}{}".format(random.random(),
                               datetime.datetime.utcnow().isoformat())
    new_hash = hashlib.md5(random_str.encode())
    entity_id = "/".join([entity_type, new_hash.hexdigest()])
    if entity_id.startswith("/"):
        entity_id = entity_exists[1:]
    entity_url = "".join([fedora_base, entity_id])
    entity_graph = rdflib.Graph()
    entity_graph.add((rdflib.URIRef(entity_url),
                      rdflib.RDF.type,
                      rdflib.URIRef("/".join(
                        ["http://schema.org",entity_type]))))
    add_stub_request = urllib.request.Request(
        entity_url,
        data=entity_graph.serialize(format='turtle'),
        method='PUT',
        headers={'Content-type': 'text/turtle'})
    print("Entity url is {}".format(entity_url))
    add_response = urllib.request.urlopen(add_stub_request)
    print("Entity url is {}".format(entity_url))
    if add_response.code < 400:
        return entity_url
    else:
        raise abort(500)

@editor.route("/replace",
              methods=['POST', 'GET'])
def replace():
##    if not request.method.startswith('POST'):
##        raise abort(501)
    entity_id = request.form['entityid']
    property_name = request.form['name']
    print("Before value entity={} prop_name={}".format(entity_id,
        property_name))
    new_value = request.form['value']
    old_value = request.form['old']
    result = replace_entity_property(
        entity_id,
        property_name,
        old_value,
        new_value)
    if result is True:
        return "Success"
    return "{} {} old={} new={}".format(entity_id, property_name, new_value)

@editor.route("/update",
              methods=['POST', 'GET'])
def update():
    def filter_id(text):
        try:
            int(text[-1])
            return filter_id(text[:-1])
        except ValueError:
            return text
    if not request.method.startswith('POST'):
        raise abort(401)
    entity_id = request.form['entityid']
    property_name = filter_id(request.form['name'])
    property_value = request.form['value']
    count = request.form['count']
    result = update_entity_property(entity_id,
                                    property_name,
                                    property_value)
    if result is True:
        return "Success!"
    return "Your request {}={} for {} failed".format(property_name,
        property_name,
        property_value,
        entity_id)



@editor.route("/")
def index():
    return render_template("index.html")

def main():
    host = '0.0.0.0'
    port = 8100
    editor.run(
        host=host,
        port=port,
        debug=True)

if __name__ == '__main__':
    main()
