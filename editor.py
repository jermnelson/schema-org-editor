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
import os

from flask import abort, Flask, g, jsonify, redirect, render_template, request
from flask import url_for
from werkzeug import secure_filename

#! Temp coding hack, need to install when finished
sys.path.append("E:\\prog\\flask-fedora-commons")
from flask_fedora_commons import Repository

from string import Template

TEMP_UPLOADS = 'files/temp'
ALLOWED_EXTENSIONS = set(["PDF", "MP3"])

editor = Flask(__name__)
editor.config["UPLOAD_FOLDER"] = 'files/temp'
editor.config.from_pyfile('editor.cfg')
repo = Repository(editor)

TEMP_UPLOADS = 'files/temp'
ALLOWED_EXTENSTIONS = set(["pdf", "mp3"])

# fedora_base = 'http://172.25.1.108:8080/rest/'
fedora_base = 'http://localhost:8080/rest/schema/'
fcrepo = rdflib.Namespace('http://fedora.info/definitions/v4/repository#')
literal_set = set(['Text', 'Number', 'Date'])
schema_json = json.load(open('schema_org.json'))
schema_ns = rdflib.Namespace('http://schema.org/')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


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


@editor.route("/upload", methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        print(file)
        if file:
            filename = secure_filename(file.filename)
            #file.save(os.path.join(editor.config['UPLOAD_FOLDER'], filename))
            entity_id = request.form['entityid']
            if not entity_id.startswith("http"):
                entity_uri = urllib.parse.urljoin(fedora_base, entity_id)
            else:
                entity_uri = entity_id
            if not repo.exists(entity_id):
                repo.create(entity_id)
            sparql_template = Template("""PREFIX schema: <http://schema.org/>
            INSERT DATA {
                <$entity> $prop_name "$prop_value"
            }""")
            sparql = sparql_template.substitute(
                entity=entity_uri+"/fcr:content",
                prop_name="--upload-file",
                prop_value=file)

            update_request = urllib.request.Request(
                entity_uri,
                data=sparql.encode(),
                method='POST',
                headers={'Content-Type': 'application/sparql-update'})
            print("Before request")
            response = urllib.request.urlopen(update_request)
            print("After request")
            if response.code < 400:
                return "Success"
            return "Adding of datastream failed"
    return "Failure, not Posting, or bad file/extension"


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
