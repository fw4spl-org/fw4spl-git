# fw4spl-git
Git tools to manage contributions in fw4spl

## Sheldon

### Requirements

* [Python 2.7.x](https://www.python.org/downloads/)
* [Git](https://git-scm.com/)
* To use *codingstyle-hook*, you must install our patched version of **[Uncrustify](https://github.com/fw4spl-org/uncrustify/releases)**
* To use *cppcheck-hook*, you must install [CppCheck](http://cppcheck.sourceforge.net/)

### Presentation

Sheldon is a tool that allows to check that files or commits respect our coding guidelines:
 - [stable version](http://fw4spl.readthedocs.org/en/master/CodingStyle/index.html)
 - [latest version](http://fw4spl.readthedocs.org/en/dev/CodingStyle/index.html)

```
usage: sheldon [-h] [-f] [-v] [--with-uncrustify UNCRUSTIFY_PATH]
               [--with-cppcheck CPPCHECK_PATH] [-i INPUT_PATH]
               [path [path ...]]

Check and/or reformat code to comply to FW4SPL coding guidelines.

positional arguments:
  path           Git path, can be a commit or two commits.

optional arguments:
  -h, --help     show this help message and exit
  -f, --format   Enable code reformatting.
  -v, --verbose  Increase the verbosity level.
  --with-uncrustify UNCRUSTIFY_PATH
                        Use uncrustify from path.
  --with-cppcheck CPPCHECK_PATH
                        Use cppcheck from path.
  -i INPUT_PATH, --input INPUT_PATH
                        Check the specific file/directory, staged or not.
                        Recursive when the argument is a directory
```

The script works on git staged/modified files or directly on file/directory:

- For git mode, in three different ways depending on the number of paths:
 - If no path is specified, the current staged files are processed.
 - If 1 path is specified, the files modified in the specified path is processed.
 - If 2 paths are specified, the files modified between the two paths are processed.


- For file/directory mode, using the --input argument:
 - If the argument is a file, only this file will be checked.
 - If the argument is a directory, Sheldon will recursively check all files within this directory.

### Examples

**Example 1:**

```sh
vim main.cpp
git add main.cpp
sheldon -f
```

checks and modifies the file `main.cpp` to comply to our rules.

**Example 2:**

```sh
sheldon 511c628^!
```

check files modified in the commit 511c628.

**Example 3:**

```sh
sheldon 124e8415 511c628
```

check files modified between commits 124e8415 and 511c628.

**Example 4:**

```sh
sheldon -i main.cpp
```

checks the file `main.cpp` (current local version).

### Configuration

Sheldon configuration is stored in git config files, so you can have global,
user or repository specific settings.

**Available options are:**

- **codingstyle-hook.uncrustify-path**: path to the uncrustify binary (default to `uncrustify`, which means it should be in the global `PATH`)
- **codingstyle-hook.source-patterns**: list of files extensions matching source files (default: `*.cpp *.cxx *.c`)
- **codingstyle-hook.header-patterns**: list of files extensions matching header files (default: `*.hpp *.hxx *.h`)
- **codingstyle-hook.misc-patterns**: list of files extensions matching other files (default: `*.cmake *.txt *.xml *.json`)
- **codingstyle-hook.sort-includes**: enable or disable header includes sort (default: `true`)
- **codingstyle-hook.additional-projects**: list of additional fw4spl repositories paths used to sort includes (separated with a ;). (default: parent folder of the current repository)
- **cppcheck-hook.cppcheck-path**: path to the cppcheck binary (default to `cppcheck`, which means it should be in the global `PATH`)
- **cppcheck-hook.source-patterns**: list of files extensions matching source files (default: `*.cpp *.cxx *.c`)
- **cppcheck-hook.header-patterns**: list of files extensions matching header files (default: `*.hpp *.hxx *.h`)
- **fw4spl-hooks.hooks**: list of enables hooks amongst `crlf tab filesize oslmlog digraphs codingstyle doxygen copain check_xml cppcheck`
- **forbidtoken-hooks.crlf**: list of file extensions that should be checked for
the end of line hook (default: `*.cpp *.hpp *.hxx *.cxx *.c *.h *.xml *.txt *.cmake *.py`)
- **forbidtoken-hooks.lgpl**: list of file extensions that should be checked for
the lgpl hook  (default: `*.cpp *.hpp *.hxx *.cxx *.c *.h *.xml *.txt *.cmake`)
- **forbidtoken-hooks.tab**: list of file extensions that should be checked for
the tab hook  (default: `*.cpp *.hpp *.hxx *.cxx *.c *.h *.xml *.txt *.cmake *.py`)
- **forbidtoken-hooks.oslmlog**: list of file extensions that should be checked for
the oslm_log hook (default: `*.cpp *.hpp *.hxx *.cxx *.c *.h`)
- **forbidtoken-hooks.digraphs**: list of file extensions that should be checked for
the digraphs hook (default: `*.cpp *.hpp *.hxx *.cxx *.c *.h`)
- **forbidtoken-hooks.doxygen**: list of file extensions that should be checked for
the doyxgen hook (default: `*.cpp *.hpp *.hxx *.cxx *.c *.h`)
- **forbidtoken-hooks.copain**: list of file extensions that should be checked for
the copain hook (default: `*.cpp *.hpp *.hxx *.cxx *.c *.h`)
- **filesize-hook.max-size**: set the maximum size of files (default 1048576)
- **filesize-hook.type**: `binary` or `all` (default `all`)

Thus to change globally the path to uncrustify, you may call something like:
```bash
git config --global codingstyle-hook.uncrustify-path /home/toto/software/uncrustify/bin/uncrustify
```
