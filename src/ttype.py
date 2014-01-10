#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fcntl
import os
import ctypes
import subprocess
import sys
import struct
import argparse

TTYPE_VERSION = '1.0.0'

#-----------------------------------------------------------------------------
# This section of code is copied from:
# http://code.activestate.com/recipes/578225-linux-ioctl-numbers-in-python/

# constant for linux portability
_IOC_NRBITS = 8
_IOC_TYPEBITS = 8

# architecture specific
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRMASK = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK = (1 << _IOC_TYPEBITS) - 1
_IOC_SIZEMASK = (1 << _IOC_SIZEBITS) - 1
_IOC_DIRMASK = (1 << _IOC_DIRBITS) - 1

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2


def _IOC(dir, type, nr, size):
    """Linux ioctl numbers made easy
       size can be an integer or format string compatible with struct module
       for example include/linux/watchdog.h:
       #define WATCHDOG_IOCTL_BASE     'W'
       struct watchdog_info {
               __u32 options;          /* Options the card/driver supports */
               __u32 firmware_version; /* Firmware version of the card */
               __u8  identity[32];     /* Identity of the board */
       };
       #define WDIOC_GETSUPPORT  _IOR(WATCHDOG_IOCTL_BASE, 0, struct watchdog_info)
       becomes:
       WDIOC_GETSUPPORT = _IOR(ord('W'), 0, "=II32s")
    """
    if isinstance(size, str) or isinstance(size, unicode):
        size = struct.calcsize(size)
    return dir  << _IOC_DIRSHIFT  | \
           type << _IOC_TYPESHIFT | \
           nr   << _IOC_NRSHIFT   | \
           size << _IOC_SIZESHIFT


def _IO(type, nr): return _IOC(_IOC_NONE, type, nr, 0)
def _IOR(type, nr, size): return _IOC(_IOC_READ, type, nr, size)
def _IOW(type, nr, size): return _IOC(_IOC_WRITE, type, nr, size)
def _IOWR(type, nr, size): return _IOC(_IOC_READ | _IOC_WRITE, type, nr, size)

#-----------------------------------------------------------------------------

UINPUT_MAX_NAME_SIZE = 80
EV_SYN = 0x00
EV_KEY = 0x01
UI_SET_EVBIT = _IOW(ord('U'), 100, '=I')
UI_SET_KEYBIT = _IOW(ord('U'), 101, '=I')
UI_DEV_CREATE = _IO(ord('U'), 1)
UI_DEV_DESTROY = _IO(ord('U'), 2)

class input_id(ctypes.Structure):
    _fields_ = [
        ("bustype", ctypes.c_uint16),
        ("vendor", ctypes.c_uint16),
        ("product", ctypes.c_uint16),
        ("version", ctypes.c_uint16),
    ]

class uinput_user_dev(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char * UINPUT_MAX_NAME_SIZE),
        ("id", input_id),
        ("ff_effects_max", ctypes.c_uint32),
        ("absmax", ctypes.c_int32 * 0x40),
        ("absmin", ctypes.c_int32 * 0x40),
        ("absfuzz", ctypes.c_int32 * 0x40),
        ("absflat", ctypes.c_int32 * 0x40)
    ]

class timeval(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_usec", ctypes.c_long)]

class input_event(ctypes.Structure):
    _fields_ = [
        ("time", timeval),
        ("type", ctypes.c_uint16),
        ("code", ctypes.c_uint16),
        ("value", ctypes.c_int32)
    ]

def open_virtual_keyboard(keys):
    """Creates virtual keyboard and enables all required features.
       keys is a list of unique keycodes of the keys to be simulated.
       This function returns file descriptor to the virtual keyboard.
       References: include/uapi/linux/uinput.h
       evdev library could be used instead: http://pythonhosted.org/evdev/
    """ 

    # 1. Define virtual keyboard
    name =           'quickcmd'
    id_bustype =     bytearray.fromhex('0006') # BUS_VIRTUAL
    id_vendor =      bytearray.fromhex('0001')
    id_product =     bytearray.fromhex('0001')
    id_version =     bytearray.fromhex('0001')
    ff_effects_max = bytearray.fromhex('00000000')
    absmax =         bytearray.fromhex('00000000')
    absmin =         bytearray.fromhex('00000000')
    absfuzz =        bytearray.fromhex('00000000')
    absflat =        bytearray.fromhex('00000000')

    uidev = uinput_user_dev()

    uidev.name = name
    uidev.id.bustype = 0x06 #VIRTUAL
    uidev.id.vendor = 0x01
    uidev.id.product = 0x01
    uidev.id.version = 0x01

    # this requires root privileges
    try:
        fd = os.open('/dev/input/uinput', os.O_WRONLY | os.O_NONBLOCK)
    except OSError:
        fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)

    buf = buffer(uidev)[:]
    os.write(fd, buf)

    # 2. Declare keycodes and features to be used

    ret = fcntl.ioctl(fd, UI_SET_EVBIT, EV_KEY);
    ret = fcntl.ioctl(fd, UI_SET_EVBIT, EV_SYN);

    for key in keys:
        ret = fcntl.ioctl(fd, UI_SET_KEYBIT, key);

    # 3. Create virtual device

    # loglevel must be temporarily decreased, otherwise dmesg would be printed to the terminal
    # note that this requires root privileges
    printk_ctrl = '/proc/sys/kernel/printk'
    with open(printk_ctrl) as f:
        txt = f.readlines()[0]

    loglevels = txt.split('/t')
    current_loglevel = txt[0]
    min_loglevel = txt[2]

    with open(printk_ctrl, 'w') as f:
        f.write(min_loglevel)

    ret = fcntl.ioctl(fd, UI_DEV_CREATE) # actual syscall

    with open(printk_ctrl, 'w') as f:
        f.write(current_loglevel)

    return fd

def close_virtual_keyboard(fd):
    """Releases keyboard created by open_virtual_keyboard.
       fd is a file descriptor to the virtual keyboard.
    """
    ret = fcntl.ioctl(fd, UI_DEV_DESTROY)
    os.close(fd)

def press_keys(plan):
    """Simulates pressing keys according to the plan
       plan is a list of sequences of keycodes of the keys to be pressed, example:
       plan = [[1, 2, 3], [4], [5, 6]] will give following result:
       keycode 1 - key down
       keycode 2 - key down
       keycode 3 - key down
       keycode 3 - key up
       keycode 2 - key up
       keycode 1 - key up
       keycode 4 - key down
       keycode 4 - key up
       keycode 5 - key down
       keycode 6 - key down
       keycode 6 - key up
       keycode 5 - key up
    """

    keys = set([code for action in plan for code in action]) # list of unique keycodes
    fd = open_virtual_keyboard(keys)

    ev = input_event()
    ev.type = EV_KEY

    for action in plan:

        for code in action:
            ev.code = code
            ev.value = 1
            os.write(fd, ev) # key down

        for code in action[::-1]:
            ev.code = code
            ev.value = 0
            os.write(fd, ev) # key up

    close_virtual_keyboard(fd)


def utf8_to_keycodes(text):
    """Converts UTF-8 encoded text to sequence of keycodes.
       Such a sequence can be accepted by press_keys() function
       References: man 5 keymaps
    """

    # 1. Get keymap
    result = subprocess.check_output('dumpkeys -f -n --keys-only', shell=True)
    lines = result.splitlines()[1:]

    # 2. Parse keycodes and unicodes
    split_lines = [line.split() for line in lines]
    keycodes_str = [line[1] for line in split_lines]
    unicodes_str = [line[3:] for line in split_lines]
    keycodes = [int(code) for code in keycodes_str]
    unicodes = [[int(code[-4:], 16) % 0x0b00 for code in codes] for codes in unicodes_str]

    #print keycodes
    #print unicodes
    
    # 3. Prepare a preliminary plan
    def find_keycode(code):
        """Returns (keycode, modifier) tuples, relevant to given UTF-8 code
        """
        for i, codes in enumerate(unicodes):
            if code in codes:
                return (keycodes[i], codes.index(code))

    text_ord = [ord(x) for x in text] # list of UTF-8 codes
    raw_plan = [find_keycode(x) for x in text_ord] # List of (keycode, modifier) tuples

    #print text_ord
    #print raw_plan

    # 4. Find modifiers
    modifiers_bin = 0 # bit mask which indicates which key modifiers are in use
    for modifier in [i[1] for i in raw_plan]:
        modifiers_bin |= modifier

    bin_ones = lambda n: [x[0] for x in enumerate(bin(n)[:1:-1]) if x[1]=='1'] # Returns indices of bits which are == 1
    modifiers_indices = bin_ones(modifiers_bin)
    modifiers_keycodes = [find_keycode(0x700 + i)[0] for i in modifiers_indices]

    #print modifiers_bin
    #print modifiers_indices
    #print modifiers_keycodes

    # 5. Prepare a final plan
    plan = [[modifiers_keycodes[modifiers_indices.index(mi)] for mi in bin_ones(p[1])] + [p[0]] for p in raw_plan]

    #print plan
    return plan

def type_text(text, ignore_cr_lf, term_is_real):
    """Invokes whole procedure of typing the text
       text is to be in UTF-8 format
    """

    if ignore_cr_lf:
        text = text.replace('\r', '').replace('\n', '')

    if text:
        if term_is_real:
            plan = utf8_to_keycodes(text)
            press_keys(plan)
        else:
            os.system('echo str "' + text + '" | xte')

#-----------------------------------------------------------------------------

def detach():
    """Detaches from the command prompt where the application was called from
       In fact it moves the application to background
    """
    ppid = os.getpid() # parent pid
    cpid = os.fork()   # child pid

    if cpid == 0: # Child            
        try:
            while(True):
                os.kill(ppid, 0) # wait for parent to die
        except OSError, e:
            pass

    else: # Parent
        exit(0)

def is_term_real():
    """Reads TERM system variable to determine whether we are in "real" terminal, or in X session
    """
    term = subprocess.check_output('echo $TERM', shell=True)
    return term == 'linux\n'

def main(args):
    """Main routine
    """

    if args.version:
        print TTYPE_VERSION
        exit(0)

    if not args.foreground:
        detach()

    if args.file == '-':
        text = '' # read from stdin
    elif args.file:
        with open(args.file) as fd:
            text = fd.read()
    else:
        text = args.text

    term_is_real = is_term_real()

    if text:
        type_text(text, args.ignore_cr_lf, term_is_real)
    else:
        try:
            for line in sys.stdin:
                type_text(line, args.ignore_cr_lf, term_is_real)
        except IOError:
            raise Exception('Cannot read stdin')

#-----------------------------------------------------------------------------

description = \
"""
Reads your text from a file or stdin, or accepts it as a parameter. Then your
text is typed on a virtual keyboard so as a result, it appears in the same
terminal where you invoked ttype. The advantage comparing to 'echo' or 'cat'
is that you can edit the text in terminal, and then for instance use it as a
command. ttype accepts text which is encoded in UTF-8.

OPTIONS:
"""

epilog = \
"""
EXAMPLES:
  $ ttype my_text
  $ echo -n my_text | ttype
  $ echo my_text | ttype -n
  $ echo -n my_text | ttype -f -
  $ echo -n my_text > my_file | ttype -f my_file
  $ ttype -g my_text &

KNOWN ISSUES:
  There are problems with typing diacritical marks

AUTHOR:
  Grzegorz Krason

REPORTING BUGS:
  contact@krason.biz
"""

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=description, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter, add_help=False)

#    subparsers = parser.add_subparsers()
#    parser = subparsers.add_parser('stop', formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('text', nargs='?', help='text to be typed; if text is empty, stdin will be used\n')
    parser.add_argument('-f', '--file', help='file to be used as a source of text; file \'-\' (dash)\nmeans stdin\n\n')
    parser.add_argument('-n', '--ignore-cr-lf', action='store_true', help='\\r and \\n characters will be ignored\n\n')
    parser.add_argument('-g', '--foreground', action='store_true', help='stay in foreground before typing (don\'t move to\nbackground); you can use this option if ttype is called\nfrom a daemon\n\n')
    parser.add_argument('-V', '--version', action='store_true', help='display version information\n\n')
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='show this help message and exit\n')

    args = parser.parse_args()

    try:
        main(args)
    except Exception, e:
        print 'ERROR: ' + str(e)
        exit(1)
    except KeyboardInterrupt, e:
        exit(2)


