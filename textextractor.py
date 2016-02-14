#!/usr/bin/env python

from subprocess import Popen, PIPE
from docx import opendocx, getdocumenttext

from pdfminer.pdfinterp import (
    PDFResourceManager, PDFPageInterpreter)
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
import magic
import sys
import os


class TextExtractor:

    def __init__(self, verbose=False):
        self.verbose = verbose

    def extractPDF(self, filein):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        fp = file(filein, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()
        pages = PDFPage.get_pages(
            fp, pagenos, maxpages=maxpages, password=password,
            caching=caching, check_extractable=False)
        for page in pages:
            interpreter.process_page(page)
        fp.close()
        device.close()
        str = retstr.getvalue()
        retstr.close()
        return str

    def extract(self, file_name, file_buffer):
        self.debug("Extracting text from %s" % (file_name))

        filetype = self.get_file_type(file_buffer)

        self.debug("File type: %s" % filetype)

        if filetype is None:
            return "Invalid file type: %s\n" % filetype

        temp_file_path = os.path.join('/tmp', file_name)
        with open(temp_file_path, 'wb') as f:
            f.write(file_buffer)

        # DOC, DOCX
        if (('application/msword' in filetype) or
                ('application/vnd.openxmlformats-officedocument' in filetype)):
            if file_name[-4:] == ".doc":
                cmd = ['antiword', temp_file_path]
                p = Popen(cmd, stdout=PIPE)
                stdout, stderr = p.communicate()
                return stdout.decode('ascii', 'ignore')
            elif file_name[-5:] == ".docx":
                document = opendocx(temp_file_path)
                paratextlist = getdocumenttext(document)
                newparatextlist = []
                for paratext in paratextlist:
                    newparatextlist.append(paratext.encode("utf-8"))
                return '\n\n'.join(newparatextlist)

        # ODT
        elif 'application/vnd.oasis.opendocument.text' in filetype:
                cmd = ['odt2txt', temp_file_path]
                p = Popen(cmd, stdout=PIPE)
                stdout, stderr = p.communicate()
                return stdout.decode('ascii', 'ignore')

        # PDF
        elif 'application/pdf' in filetype:
            return self.extractPDF(temp_file_path)

        else:
            return None

    def save_output(self, filename, output):
        if len(output) <= 0:
            sys.stderr.write("No text extracted from %s\n" % filename)
            sys.exit(0)

        try:
            f = open(filename, 'w')
            f.write(output)
            f.close()
        except Exception as e:
            self.debug("Exception: %s" % e)

    def get_file_type(self, buffer):
        return magic.from_buffer(buffer, mime=True)

    def debug(self, msg):
        if self.verbose:
            sys.stdout.write(msg + "\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="""This script is used to extract text from
        PDF, DOC, and DOCX file formats.""")
    parser.add_argument(
        '-i',
        '--input',
        help='Input file name',
        required=True)
    parser.add_argument(
        '-o',
        '--output',
        help='Output file name',
        required=True)
    parser.add_argument(
        '-v',
        '--verbose',
        help='Display debugging messages',
        action='store_true',
        default=False)
    args = parser.parse_args()

    t = TextExtractor(args.verbose)
    with open(args.input, 'rb') as f:
        file_buffer = f.read()
    output = t.extract(args.input, file_buffer)

    if not output[0]:
        print output[1]
        sys.exit()

    f = open(args.output, 'w')
    f.write(output[1])
    f.close()
