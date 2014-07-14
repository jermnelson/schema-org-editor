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



@editor.route("/id/new")
def new_id():
    random_str = "{}{}".format(random.random(),
                               datetime.datetime.utcnow().isoformat())
    new_hash = hashlib.md5(random_str.encode())
    return new_hash.hexdigest()

@editor.route("/update",
              methods=['POST', 'GET'])
def update():
    if not request.method.startswith('POST'):
        raise abort(401)
    entity_id = request.form['entityid']
    property_name = request.form['name']
    property_value = request.form['value']
    result = update_entity_property(entity_id,
                                    property_name,
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
