#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import subprocess

def note(msg):
    print('*** [Pre-commit hook] ' + msg + ' ***')

def error(msg):
    print('*** [Pre-commit hook: ERROR] ' + msg + ' ***')

def execute_command(proc):

    try:
        out = subprocess.check_output(proc.split())
    except subprocess.CalledProcessError:
        error("Command '" + proc + "' returned an error (see above for the output).")
        error("Commit aborted !!!")
        exit(1)
    return out

def get_option(option, default="", type=""):

    try:
        out = subprocess.check_output(('git config ' + type + option).split())
        return out
    except subprocess.CalledProcessError:
        if default:
            return default
        else:
            error("Option '" + option + "' not found and no default value was provided.")
            error("Commit aborted !!!")
            exit(1)

def get_file_content(path):

    file = open(path, 'rb')
    content = file.read()
    file.close()

    return content
