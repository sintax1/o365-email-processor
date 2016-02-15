# -*- coding: utf-8 -*-
"""Project metadata

Information describing the project.
"""

# The package name, which is also the "UNIX name" for the project.
package = 'o365_email_processor'
project = "Office 365 Email Processor"
project_no_spaces = project.replace(' ', '')
version = '0.2'
description = """Pulls emails from Office 365, stores them in a database,
    and processes with user defined actions"""
authors = ['Craig Koroscil']
authors_string = ', '.join(authors)
emails = ['sintax@obscurepacket.org']
license = 'MIT'
copyright = '2016 ' + authors_string
url = 'https://github.com/sintax1/o365-email-processor'
