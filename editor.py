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
import json
import uuid
import urllib

from flask import abort, Flask, g, jsonify, redirect, render_template, request
from flask import url_for

from string import Template

editor = Flask(__name__)

fedora_base = 'http://localhost:8080/rest/'

schema_json = json.load(open('schema_org.json'))

def create_entity(uuid):
    create_request = urllib.request.Request()

def entity_exists(uuid):
    entity_uri = urllib.parse.urljoin(fedora_base, uuid)
    try:
        urllib.request.urlopen(entity_uri)
        return True
    except urllib.error.HTTPError:
        return False

def update_entity_property(uuid, property_name, value):
    entity_uri = urllib.parse.urljoin(fedora_base, uuid)
    if not entity_exists(uuid):
        create_entity(uuid)
    sparql_template = Template("""PREFIX schema: <http://schema.org/>
    INSERT DATA {
        <$entity> $prop_name "$prop_value"
    }""")
    sparql = sparql_template.substitute(
        entity=entity_uri,
        prop_name=property_name,
        prop_value=value)
    update_request = urllib.request.Request(
        entity_uri,
        data=sparql.encode(),
        method='PATCH',
        headers={'Content-Type': 'application/sparql-update'})
    response = urllib.request.urlopen(update_request)



@editor.route("/uuid/new")
def new_uuid():
    return str(uuid.uuid1())

@editor.route("/update",
              methods=['POST', 'GET'])
def update():
    if not request.method.startswith('POST'):
        raise abort(401)
    uuid = request.form['uuid']
    property_name = request.form['name']
    property_value = request.form['value']
    return "Your request {}={} for {}".format(property_name,
        property_value,
        uuid)




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
