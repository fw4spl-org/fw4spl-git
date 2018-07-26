#!/usr/bin/env python3
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
Runs the check on the <config> tree.
- check if the objects are used by a service
- check if the services with autoConnect="yes" has inputs
- check if each service is used in the configuration
"""


def check_configurations(tree):
    err = ""

    # The tree's root could be <plugin> or <extension>
    configs = tree.findall("./config")
    configs += tree.findall("./extension/config")

    for config in configs:
        err += check_unused_object(config)
        err += check_autoConnect(config)
        err += check_unused_service(config)

    return err


"""
Check if the objects are used by a service in a configuration.
The tree root must be <config>
"""


def check_unused_object(config_tree):
    err = ""

    if not config_tree.tag == "config":
        err = "Cannot parse the configuration with the root " + config_tree.tag + "\n"
        return err

    # find all objects
    objects = config_tree.findall("./object")

    # find all inputs, inouts, outputs
    inouts = config_tree.findall("./service/inout")
    inouts += config_tree.findall("./service/inout/key")  # for inout group
    inouts += config_tree.findall("./service/in")
    inouts += config_tree.findall("./service/in/key")  # for in group
    inouts += config_tree.findall("./service/out")
    inouts += config_tree.findall("./service/out/key")  # for out group

    for obj in objects:
        uid = obj.get("uid")
        objfound = False

        for inout in inouts:
            inout_uid = inout.get("uid")
            if inout_uid == uid:
                objfound = True
                break

        if not objfound:
            err += "- object '" + uid + "' is not used.\n"

    return err


"""
Check if the services with autoConnect="yes" has inputs/
The tree root must be <config>
"""


def check_autoConnect(config_tree):
    err = ""
    services = config_tree.findall("./service")

    for srv in services:
        uid = srv.get("uid")
        connect = srv.get("autoConnect")

        if connect == "yes":

            inouts = srv.findall("inout") + srv.findall("in")
            if not inouts:
                err += "- service '" + uid + "' has no input, it must not be auto-connected.\n"
    return err


"""
Check if each service is used in the configuration
The tree root must be <config>
"""


def check_unused_service(config_tree):
    err = ""

    services = config_tree.findall("./service")
    parameters = config_tree.findall("./service/parameter")
    starts = config_tree.findall("./start")
    starts += config_tree.findall("./service/start")  # for SStarter
    starts += config_tree.findall("./service/start_or_stop")  # for SStarter
    starts += config_tree.findall("./service/start_only")  # for SStarter
    starts += config_tree.findall("./service/stop")  # for SStarter
    views = config_tree.findall("./service/registry/view")
    views += config_tree.findall("./service/registry/menuItem")
    views += config_tree.findall("./service/registry/editor")
    views += config_tree.findall("./service/registry/menu")
    views += config_tree.findall("./service/registry/toolBar")
    views += config_tree.findall("./service/registry/menuBar")
    slots = config_tree.findall("./service/slots/slot")  # SSlotCaller
    slots += config_tree.findall("./connect/signal")
    slots += config_tree.findall("./connect/slot")

    uids = []

    for start in starts:
        uids += [start.get("uid")]

    for view in views:
        uids += [view.get("sid")]

    for param in parameters:
        uids += [param.get("uid")]

    for slot in slots:
        match = common.re.match(r"(\w+)", slot.text)
        if (match):
            uids += [match.group(0)]

    for srv in services:

        srv_found = False

        srv_uid = srv.get("uid")

        if srv_uid is None:
            type = srv.get("type")
            err += "- 'uid' is not defined for the service '" + type + "'"
            break

        for uid in uids:
            if srv_uid == uid:
                srv_found = True
                break

        if not srv_found:
            err += "- service '" + srv_uid + "' is not used.\n"

    return err


def check_xml(files):
    abort = False

    for f in files:
        if f.path.lower().endswith(('.xml', '.xsd')):
            content = f.contents
            common.trace('Checking ' + str(f.path) + ' syntax...')
            try:
                tree = xml_parser(content.decode())
                msg = check_configurations(tree)
                if msg:
                    common.error('XML parsing error in ' + f.path + ' :\n' + msg)
                    abort = True
            except ET.ParseError as err:
                common.error('XML parsing error in ' + f.path + ' :\n' + err.msg + '\n')
                abort = True

    return abort


hooks = {
    'check_xml': check_xml,
}
