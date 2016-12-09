
'''hooks to check XML syntax

[hooks]
pretxncommit.check_xml = python:/path-to/hooks:check_xml
'''

SEPARATOR = '%s\n' % ('-'*79)

from xml.etree import ElementTree as ET

import common

def xml_parser(content):
    try:
        tree = ET.fromstring(content)
    except ET.ParseError as err:
        lineno, column = err.position
        line = content.splitlines()[lineno-2]
        caret = '{:=>{}}'.format('^', column)
        err.msg = '{}\n{}\n{}'.format(err, line, caret)
        raise
    return tree


def check_xml(files):
    abort = False

    for f in files:
        if f.path.lower().endswith(('.xml', '.xsd')):
            content = f.contents
            common.trace('Checking ' + str(f.path) + ' syntax...')
            try:
                tree = xml_parser(content)
            except ET.ParseError as err:

                common.error('XML parsing error in ' + f.path + ' :\n ' + err.msg + '\n.')
                abort = True

    return abort

hooks = {
        'check_xml':check_xml,
        }

