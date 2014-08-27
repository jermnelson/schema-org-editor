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
import sys
import urllib
import uuid

from flask import abort, Flask, g, jsonify, redirect, render_template, request
from flask import url_for

#! Temp coding hack, need to install when finished
sys.path.append("E:\\prog\\flask-fedora-commons")
from flask_fedora_commons import Repository

from string import Template

editor = Flask(__name__)
editor.config.from_pyfile('editor.cfg')
repo = Repository(editor)

# fedora_base = 'http://172.25.1.108:8080/rest/'
fedora_base = 'http://localhost:8080/rest/schema/'
fcrepo = rdflib.Namespace('http://fedora.info/definitions/v4/repository#')
literal_set = set(['Text', 'Number', 'Date'])
schema_json = json.load(open('schema_org.json'))
schema_ns = rdflib.Namespace('http://schema.org/')


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
    return repo.as_json(url)


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
    return repo.as_json('/'.join([
        fedora_base,
        entity_type,
        entity_id]))




@editor.route("/id/new/<entity_type>")
def new_id(entity_type):
    entity_id = "/".join([entity_type, str(uuid.uuid4())])
    if entity_id.startswith("/"):
        entity_id = entity_id[1:]
    entity_url = "".join([fedora_base, entity_id])
    entity_graph = rdflib.Graph()
    entity_graph.add((rdflib.URIRef(entity_url),
                      rdflib.RDF.type,
                      rdflib.URIRef("/".join(
                        ["http://schema.org",entity_type]))))
    response_uri = repo.create(entity_url, entity_graph)
    if response_uri is not None:
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
    new_value = request.form['value']
    old_value = request.form['old']
    result = repo.replace(
        entity_id,
##        property_name,
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
    result = repo.update(entity_id,
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
