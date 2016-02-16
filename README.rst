=========================
 o365 Email Processor
=========================

This project provides a service for polling email from Office 365 (via API 1.0) at a regular interval. Each email is stored in a database and sent to user defined actions for processing.

 A couple use cases:

 * Preventing malware from running which is embedded within email attachments (pdf, doc, odt) by extracting and forwarding on the text only.

 * Sending email attachments to Cuckoo's scanner via an API before forwarding on the attachment.

Installation
=============

Follow the instructions below to get the Office 365 email processor up and 
running.

Instructions
------------

#. Download this project:

    Using git::

        git clone https://github.com/sintax1/o365-email-processor.git
        cd o365-email-processor

    Using wget::

        wget https://github.com/sintax1/o365-email-processor/archive/master.zip
        unzip master.zip
        cd o365-email-processor-master

#. Install system requirements::

    sudo apt-get install antiword odt2txt libpq-dev python-dev gcc \
        libjpeg-dev libxml2-dev libxslt-dev

#. Create a virtual environment::

    sudo pip install virtualenv
    virtualenv env
    source env/bin/activate

#. Install python packages::

    python setup.py build && python setup.py install

#. Install database backend::

    sudo apt-get install postgresql-9.3

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

#. *(Optional, but recommended)* Deploy in a production environment: http://flask.pocoo.org/docs/0.10/deploying/


Usage
=============

#. Login::

    http://<server ip>:8080/login/

![Screenshot](https://cloud.githubusercontent.com/assets/6936112/13087819/50bc2db4-d4af-11e5-82c2-2efd1ed0475d.png "Welcome")
![Screenshot](https://cloud.githubusercontent.com/assets/6936112/13087829/5526fa00-d4af-11e5-8140-9d5df1d33785.png "Login")
    
#. Review/Add any actions for email processing::

    http://<server ip>:8080/actionmodelview/list/

![Screenshot](https://cloud.githubusercontent.com/assets/6936112/13087828/550e78fe-d4af-11e5-8ad5-038b9a505c7b.png "Actions")
![Screenshot](https://cloud.githubusercontent.com/assets/6936112/13087827/54f2f3e0-d4af-11e5-927e-0609a570b14c.png "Text Extraction Action")

#. Configure the system settings::

    http://<server ip>:8080/appsettingsmodelview/list/

![Screenshot](https://cloud.githubusercontent.com/assets/6936112/13087825/54be0b4e-d4af-11e5-8650-5d82056c6039.png "Settings")

#. Query/Analyze emails in the database::

    http://<server ip>:8080/emailmodelview/list/

![Screenshot](https://cloud.githubusercontent.com/assets/6936112/13087826/54d78fc4-d4af-11e5-8229-9b0f76f71f80.png "Emails")


Issues
======

Please report any bugs or requests that you have using the GitHub issue tracker!

Authors
=======

* Craig Koroscil
