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

from flask import abort, Flask, g, jsonify, redirect, render_template, request
from flask import url_for

editor = Flask(__name__)

schema_json = json.load(open('schema_org.json'))

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
