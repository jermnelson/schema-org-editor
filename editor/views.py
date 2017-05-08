__author__ = "Jeremy Nelson"

import os
import rdflib
import sys
import uuid

from flask import Blueprint, render_template, abort
from flask_wtf import FlaskForm
from jinja2 import TemplateNotFound
from types import SimpleNamespace
from wtforms import BooleanField, DateField, SelectField, StringField
from wtforms.validators import Optional

schema_editor = Blueprint("schema_editor", 
    __name__,
    static_folder='static',
    static_url_path='/static/schema_editor',
    template_folder='templates')

EDITOR_HOME = os.path.abspath(os.path.dirname(__file__))

SCHEMA = rdflib.Namespace("http://schema.org/")
SCHEMA_VOCAB = rdflib.Graph()
SCHEMA_VOCAB.parse(os.path.join(EDITOR_HOME, "static/rdf/schema.ttl"),
    format='turtle')

OUTPUT = rdflib.Graph()
OUTPUT.namespace_manager.bind('schema', SCHEMA)

def get_properties(class_iri):
    properties = []
    for row in SCHEMA_VOCAB.query(PROP_QUERY,
        initBindings={"classOf": class_iri}):
        properties.append(row[0])
    for parent_iri in SCHEMA_VOCAB.objects(subject=class_iri,
        predicate=rdflib.RDFS.subClassOf):
        properties.extend(get_properties(parent_iri))
    return sorted(properties)

def guess_field(iri):
    label = SCHEMA_VOCAB.value(subject=iri,
        predicate=rdflib.RDFS.label)
    ranges = [o for o in SCHEMA_VOCAB.objects(subject=iri,
        predicate=SCHEMA.rangeIncludes)]
    for row in ranges:
        if row == SCHEMA.Text:
            field = StringField(label)
            break
        elif row == SCHEMA.Boolean:
            field = BooleanField(label)
            break
        elif row in [SCHEMA.DateTime, SCHEMA.Time, SCHEMA.Date]:
            field = DateField(label, validators=[Optional()])
            break
        class_ = SCHEMA_VOCAB.value(subject=row, 
            predicate=rdflib.RDF.type)
        if class_ == rdflib.RDFS.Class:
            choices = [('none', "None")]
            for iri in OUTPUT.subjects(predicate=rdflib.RDF.type,
                object=row):
                choices.append(
                    (iri, 
                    OUTPUT.value(subject=iri, predicate=SCHEMA.name)))
            field = SelectField(label, choices=choices, default='none')
    return field
    

@schema_editor.route("/<thing>", 
    methods=["POST", "GET"])
def edit(thing):
    class ThingForm(FlaskForm):
        pass
    thing_iri = getattr(SCHEMA, thing)
    thing_label = SCHEMA_VOCAB.value(subject=thing_iri, 
        predicate=rdflib.RDFS.label)
    for prop_iri in get_properties(thing_iri):
        setattr(ThingForm, str(prop_iri), guess_field(prop_iri))
    form = ThingForm()
    if form.validate_on_submit():
        new_iri = rdflib.URIRef("https://peopleuid.com/{}".format(uuid.uuid1()))
        OUTPUT.add((new_iri, rdflib.RDF.type, thing_iri))
        for key, value in form.data.items():
            if str(key).startswith("csrf_token"):
                continue
            if value is not None and not str(value).startswith("none") and len(str(value)) > 0: 
                OUTPUT.add((new_iri, rdflib.URIRef(key), rdflib.Literal(value)))
        return "{}".format(OUTPUT.serialize(format='turtle').decode())
    return render_template("editor/read.html", 
        iri=thing_iri,
        label=thing_label,
        form=form)


@schema_editor.route('/')
def home():
    return render_template("editor/index.html",
        vocab=None)
    
PROP_QUERY = """SELECT ?prop
WHERE {
  ?prop schema:domainIncludes ?classOf ;
        rdfs:label ?label .
} ORDER BY ?label"""
