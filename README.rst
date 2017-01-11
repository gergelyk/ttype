=====
ttype
=====

Replacement of echo/cat command that types using virtual keyboard instead of printing to stdout 

Overview
--------

Reads your text from a file or stdin, or accepts it as an argument. Then your text is typed on a virtual keyboard in the same terminal where you invoked ttype.

Behavior of ttype is similar to 'echo' or 'cat' with this difference that your text doesn't go to stdout. Instead of that it can be edited in terminal and used for instance as a command.

Features
--------

* Works in both, Linux console and in X Window System terminals
* Supports UTF-8

More Info
---------

For information about usage invoke ttype -h

$ sudo make install
$ make export

