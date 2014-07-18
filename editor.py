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

fedora_base = 'http://localhost:8080/rest/'

schema_json = json.load(open('schema_org.json'))
schema_ns = rdflib.Namespace('http://schema.org/')

def create_entity(entity_id):
    entity_url = urllib.parse.urljoin(fedora_base, entity_id)
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
                            value):
    entity_uri = urllib.parse.urljoin(fedora_base, entity_id)
    if 'URL' in schema_json['properties'][property_name]['ranges']:
        sparql_template = Template("""PREFIX schema: <http://schema.org/>
        DELETE {
         <$entity> $prop_name <$prop_value>
        } INSERT {
         <$entity> $prop_name <$prop_value>
        } WHERE {
        }""")

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
    entity_uri = urllib.parse.urljoin(fedora_base, entity_id)
    if not entity_exists(entity_id):
        create_entity(entity_id)
    if 'URL' in schema_json['properties'][property_name]['ranges']:
        sparql_template = Template("""PREFIX schema: <http://schema.org/>
    INSERT DATA {
        <$entity> $prop_name <$prop_value>
    }""")
    else:
        sparql_template = Template("""PREFIX schema: <http://schema.org/>
    INSERT DATA {
        <$entity> $prop_name "$prop_value"
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


@editor.route("/id/<entity_type>/<entity_id>")
def get_entity(entity_type, entity_id):
    entity_url = '/'.join([fedora_base, entity_type, entity_id])
    entity_graph = rdflib.Graph().parse(entity_url)
    entity_json = json.loads(entity_graph.serialize(format='json-ld').decode())
    return json.dumps(entity_json)




@editor.route("/id/new/<entity_type>")
def new_id(entity_type):
    random_str = "{}{}".format(random.random(),
                               datetime.datetime.utcnow().isoformat())
    new_hash = hashlib.md5(random_str.encode())
    entity_id = "/".join([entity_type, new_hash.hexdigest()])
    entity_url = "".join([fedora_base, "/{}".format(entity_id)])
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
    add_response = urllib.request.urlopen(add_stub_request)
    if add_response.code < 400:
        return entity_id
    else:
        raise abort(500)

@editor.route("/replace",
              methods=['POST'])
def replace():
    entity_id = request.form['entityid']
    property_name = request.form['name']
    new_value = request.form['value']
    old_value = request.form['old']
    return "{} {} old={} new={}".format(entity_id, property_name, new_value, new_id)

@editor.route("/update",
              methods=['POST', 'GET'])
def update():
    if not request.method.startswith('POST'):
        raise abort(401)
    entity_id = request.form['entityid']
    property_name = request.form['name']
    property_value = request.form['value']
    count = request.form['count']
    result = update_entity_property(entity_id,
                                    property_name[:-1],
                                    property_value)
    if result is True:
        return "Success!"
    return "Your request {}={} for {}".format(property_name,
        property_value,
        entity_id)




@editor.route("/")
def index():
    return render_template("index.html",
                           schema=json.dumps(schema_json))

def main():
    host = '0.0.0.0'
    port = 8100
    editor.run(
        host=host,
        port=port,
        debug=True)

if __name__ == '__main__':
    main()
