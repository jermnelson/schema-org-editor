# README for Schema.org Web Editor

[![Build Status](https://travis-ci.org/jermnelson/flask-fedora-commons.svg)](https://travis-ci.org/jermnelson/flask-fedora-commons)

This project is a simple HTML5 editor for [schema.org][SCHEMA]  metadata. 

## Installing
Currently the only method of running the editor is cloning the source code from Github.

    >> git clone https://github.com/jermnelson/schema-org-editor.git


## Getting Started
The Schema.org web editor will use a locally running instance of [Fedora 4][FEDORA]. The 
default local location running location of [Fedora 4][FEDORA] is a <http://localhost:8080>.
This location can be changed by setting the base_url in a new **editor.cfg** configuration file.
Make sure that **editor.cfg** filed exists in the schema-org-editor directory.

Setup the editor from the command-line for the first time will display the editor locally at
<http://localhost:8100>

    >> cd schema-org-editor
    >> python editor.py

[FEDORA]: http://fedora-commons.org/
[SCHEMA]: http://schema.org/
