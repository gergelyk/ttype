### Commented entries have reasonable defaults.
### Uncomment to edit them.
# Source: <source package name; defaults to package name>
# Section: misc
# Priority: optional
Homepage: http://www.krason.biz/#ttype
Standards-Version: 3.9.2

Package: ttype
Version: 1.0.0
Maintainer: Grzegorz Krason <contact@krason.biz>
# Pre-Depends: <comma-separated list of packages>
Depends: libc6 (>= 2.7), xautomation (>= 1.03-1.1), console-tools(>= 1:0.2.3dbs-70), x11-xkb-utils(>= 7.7~1)
# Recommends: <comma-separated list of packages>
# Suggests: <comma-separated list of packages>
# Provides: <comma-separated list of packages>
# Replaces: <comma-separated list of packages>
Architecture: amd64
# Copyright: <copyright file; defaults to GPL2>
# Changelog: <changelog file; defaults to a generic changelog>
Readme: README.Debian
# Extra-Files: <comma-separated list of additional files for the doc directory>
Files: ../bin/ttype /usr/bin
 ../man1/ttype.1.gz /usr/share/man/man1

Description: Types user's text on a virtual keyboard
 Reads your text from a file or stdin, or accepts it as a parameter. Then
 your text is typed on a virtual keyboard so as a result, it appears in the
 same terminal where you invoked ttype. The advantage comparing to 'echo' or
 'cat' is that you can edit the text in terminal, and then for instance use it
 as a command. ttype accepts text which is encoded in UTF-8.

File: postinst
 #!/bin/sh -e
 chown root:root /usr/bin/ttype
 chmod +s /usr/bin/ttype


