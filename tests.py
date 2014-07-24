#-------------------------------------------------------------------------------
# Name:        tests
# Purpose:     Schema.org Editor Unit tests
#
# Author:      Jeremy Nelson
#
# Created:     2014/07/14
# Copyright:   (c) Jeremy Nelson, Colorado College 2014
# Licence:     MIT
#-------------------------------------------------------------------------------

import editor
import unittest
import urllib.request

class TestEntityFunctions(unittest.TestCase):

    def setUp(self):
        self.test_entity_uri = "/".join([editor.fedora_base, 'Test', 'Work1'])

    def test_create_entity(self):
        self.assertEqual(
            self.test_entity_uri,
            editor.create_entity(self.test_entity_uri))

    def test_entity_exists(self):
        editor.create_entity(self.test_entity_uri)
        self.assertTrue(editor.entity_exists(self.test_entity_uri))
        nonexisting_uri = "/".join([editor.fedora_base, 'Test', 'Work2'])
        self.assertFalse(editor.entity_exists(nonexisting_uri))

    def test_update_entity_property(self):
        editor.create_entity(self.test_entity_uri)





    def tearDown(self):
        fedora_test_uri = "/".join([editor.fedora_base, 'Test'])
        delete_request = urllib.request.Request(
            fedora_test_uri,
            method='DELETE')
        fedora_response = urllib.request.urlopen(delete_request)



if __name__ == '__main__':
    unittest.main()
