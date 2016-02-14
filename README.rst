=========================
 o365 Email Processor
=========================

This project provides a service for polling email from Office 365 (via API 1.0) at a regular intervale. Each email is stored in a database and sent to user defined actions for processing.

 A couple use cases:

 * Preventing malware from running that is embedded in document attachments 
   by extracting and forwarding on the text only.

 * Sending every attachment to Cuckoo's scanner via API before forwarding on
   the attachment.

Project Setup
=============

Follow the instructions below to get the Office 365 email processor up and 
running.

Instructions
------------

#. Clone the o365 email processor project:

    Using git::

        git clone https://github.com/sintax1/o365-email-processor.git
        cd o365-email-processor

    Using wget::

        wget https://github.com/sintax1/o365-email-processor/archive/master.zip
        unzip master.zip
        cd o365-email-processor

#. Install system requirements::

    sudo apt-get install virtualenv antiword odt2txt libpq-dev python-dev gcc \
        libjpeg-dev libxml2-dev libxslt-dev

#. Create a virtual environment::

    virtualenv env
    source env/bin/activate

#. Install python packages::

    python setup.py build && python setup.py install

#. Install database backend::

    sudo apt-get install postgresql-9.4

#. Configure the database. Replace ``[DB USER]`` and ``[DB PASSWORD]`` with your settings::

    sudo su - postgres
    psql
    postgres=# CREATE DATABASE email_processor;
    postgres=# CREATE USER [DB USER] WITH PASSWORD '[DB PASSWORD]';
    postgres=# GRANT ALL PRIVILEGES ON DATABASE email_processor TO [DB USER];
    postgres=# \q
    exit

#. Modify ``config.py`` for your environment::

    vim config.py # Modify database connection information

#. Build the database tables::

    fabmanager create-db

#. Create an admin account::

    fabmanager create-admin

#. Start the web server::

    python run.py

#. Login and configure email settings::

    http://<server ip>:8080/login/

Licenses
========

Issues
======

Please report any bugs or requests that you have using the GitHub issue tracker!

Development
===========

Authors
=======

* Craig Koroscil
