# fw4spl-git
Git tools to manage contributions in fw4spl

## Sheldon

Sheldon is a tool that allows to check that files or commits respect our [coding
guidelines](http://fw4spl.readthedocs.io/en/fw4spl_0.11.0/CodingStyle/index.html).

```
usage: sheldon [-h] [-f] [-v] [path [path ...]]

positional arguments:
  path           Git path, can be a commit or two commits.

optional arguments:
  -h, --help     show this help message and exit
  -f, --format   Enable code reformatting.
  -v, --verbose  Increase the verbosity level.
```

It can be invoked in three different ways, depending on the number of paths:
- If no path is specified, the current staged files are processed.
- If 1 path is specified, the files modified in the specified path is processed.
- If 2 paths are specified, the files modified between the two paths are processed.

Example 1:

```sh
vim main.cpp
git add main.cpp
sheldon -f
```

checks and modifies the file `main.cpp` to comply to our rules.

Example 2:

```sh
sheldon 511c628^!
```

check files modified in the commit 511c628.

Example 3:

```sh
sheldon 124e8415 511c628
```

check files modified between commits 124e8415 and 511c628.

Sheldon configuration is stored in git config files, so you can have global,
user or repository specific settings.

Available options are:
- **codingstyle-hook.uncrustify-path**: path to the uncrustify binary (default to `uncrustify`, which means it should be in the global `PATH`)
- **codingstyle-hook.source-patterns**: list of files extensions matching source files (default: `*.cpp *.cxx *.c`)
- **codingstyle-hook.header-patterns**: list of files extensions matching header files (default: `*.hpp *.hxx *.h`)
- **codingstyle-hook.misc-patterns**: list of files extensions matching other files (default: `*.cmake *.txt *.xml *.json`)
- **codingstyle-hook.sort-includes**: enable or disable header includes sort (default: `true`)
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
