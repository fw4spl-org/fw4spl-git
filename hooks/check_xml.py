#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""

hooks to check XML syntax

[hooks]
pretxncommit.check_xml = python:/path-to/hooks:check_xml

"""

from xml.etree import ElementTree as ET

import common

SEPARATOR = '%s\n' % ('-' * 79)


def xml_parser(content):
    try:
        tree = ET.fromstring(content)
    except ET.ParseError as err:
        line_number, column = err.position
        line = content.splitlines()[line_number - 2]
        caret = '{:=>{}}'.format('^', column)
        err.msg = '{}\n{}\n{}'.format(err, line, caret)
        raise
    return tree

"""
check if the objects are used by a service
"""
def check_unused_object(tree):
    err = ""

    # find all objects
    objects = tree.findall("./extension/config/object")

    # find all inputs, inouts, outputs
    inouts = tree.findall("./extension/config/service/inout")
    inouts += tree.findall("./extension/config/service/inout/key") # for inout group
    inouts += tree.findall("./extension/config/service/in")
    inouts += tree.findall("./extension/config/service/in/key") # for in group
    inouts += tree.findall("./extension/config/service/out")
    inouts += tree.findall("./extension/config/service/out/key") # for out group

    for obj in objects:
        uid=obj.get("uid")
        objfound=False

        for inout in inouts:
            inout_uid=inout.get("uid")
            if inout_uid == uid:
                objfound=True
                break

        if not objfound:
            err += "- object '" + uid + "' is not used.\n"

    return err

"""
check if the service with autoConnect="yes" has inputs
"""
def check_autoConnect(tree):
    err=""
    services = tree.findall("./extension/config/service")
    for srv in services:
        uid = srv.get("uid")
        connect = srv.get("autoConnect")
        if connect:

            inouts = srv.findall("inout") + srv.findall("in")
            if not inouts:
                err += "- service '" + uid + "' has no input, it must not be auto-connected.\n"
    return err

def check_xml(files):
    abort = False

    for f in files:
        if f.path.lower().endswith(('.xml', '.xsd')):
            content = f.contents
            common.trace('Checking ' + str(f.path) + ' syntax...')
            try:
                tree = xml_parser(content)
            except ET.ParseError as err:

                common.error('XML parsing error in ' + f.path + ' :\n' + err.msg + '\n')
                abort = True

            msg = check_unused_object(tree)
            msg += check_autoConnect(tree)
            if msg:
                common.error('XML parsing error in ' + f.path + ' :\n' + msg)

    return abort


hooks = {
    'check_xml': check_xml,
}
