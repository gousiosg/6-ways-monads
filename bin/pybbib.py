# Original code by Adriaan de Groot. 
#
# Disributed under the BSD license
#
# Functions to parse/write BiBTeX files

import string, os, sys

# report errors by throwing this exception
class BibError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


# open a bib file
def bib_open(file):
    bibname = os.path.splitext (file) [0] + '.bib'
    try:
        bibf = open (bibname, 'r')
    except IOError, err:
        raise BibError, "File does not exist"
    return bibf

# Parsing/scanning bib file and keeping track of current char, line number
# etc.

# contains a single bibfile as a single string
buffer = ""
# pointer to the current character to be read
cur = 0
# line number corresponding to the current character to be read
lineno = 0
# last bibtex key successfully parsed
lastsuccessfulkey = ""


# open a bibfile and initialise the scan buffer
def initch(file):
    global buffer, cur, lineno
    f = bib_open(file)
    buffer = f.read()
    cur = 0
    lineno = 1

# get the current character on the input, None of EOF    
def curch():
    global buffer, cur
    if cur < len(buffer):
        return buffer[cur]
    else:
        return None

# advance to the next character on the input    
def nextch():
    global cur, lineno
    if curch() == "\n":
        lineno = lineno + 1 
    cur = cur + 1
    
# skip a comment: all characters upto the next end of line
def skip_comment():
    while curch() <> '\n':
        nextch()

# skip whitespace; this includes comments (but not EOF).
# curch() returns the first nonwhitespace char, or None if at EOF
def skip_whitespace():
    while (curch() <> None) and ((curch() == "%") or (curch() in string.whitespace)):
        if curch() == '%':
            skip_comment()
        nextch()

# skip whitespace and check if the next char on the input is in s
# if so, return it, and advance the character pointer.
# If not or at EOF, return None
def expect(s):
    skip_whitespace()
    c = curch()
    if c == None:
        return None
    if c not in s:
        return None
    else:
        nextch()
        return c

# skip whitespace and check if the next char on the input is in s
# if so, return it, and advance the character pointer.
# If not or at EOF, report an error.
def required(s):
    global lastsuccessfulkey
    skip_whitespace()
    c = curch()

    if c not in s:
        raise BibError, "Expecting %s (after entry %s)" % (s, lastsuccessfulkey)
    nextch()
    return c

# the characters that may appear in a name; this is NOT COMPLETE
name_letters = string.ascii_letters + string.digits + "?_-+:;*."

# skip leading whitespace and read a name/key, and return it. curch()
# points to the first non-name char. if at EOF, return None
def bib_getname():
    ret = expect(name_letters)
    if ret == None:
        return None
    name = ret
    while curch() in name_letters:
        name = name + curch()
        nextch()
    return name

# Get the value for a bibtex field. Instead of parsing the field, we use
# the following rule: a field is terminated by either a "," or a "}"
# (which is not following a "\"), unless either of them occurs within a quoted
# context (ie inside an unclosed { or ")
# Return the value as a string. curch() points to the first char not part
# of the value (ie "," or "}")
def bib_getvalue():
    lastch = ""
    s = ""
    symstack = []
    while ( not curch() is None) and ( symstack <> [] or ( curch() not in [",", "}"] )) :
        s = s + curch()
        if lastch <> "\\":
            if curch() == "{":
                symstack.append("{")
            elif curch() == "\"":
                if (symstack <> []) and (symstack[-1] == "\""):
                    symstack.pop()
                else:
                    symstack.append("\"")
            elif curch() == "}" and symstack <> [] and symstack[-1] == "{":
                symstack.pop()
        lastch = curch()
        nextch()
    return s
    
# return the next (fieldname,value) pair, or None if not at a fieldname
def bib_getfield():
    fieldname = bib_getname()
    if fieldname == None:
        return None
    required("=")
    skip_whitespace()
    value = bib_getvalue()
    return (fieldname, value)

# return the next entry as a dictionary, with fields "mytype" and "mykey"
# for the type and key respectively, or None if no more entries
def bib_getentry():
    global lastsuccessfulkey
    entry = {}
    if expect("@") == None:
        return None
    tp = ""
    tp = bib_getname()
    entry["mytype"]= tp
    required("{")
    # strings must be ignored and do not have a key
    if tp != "string":
        key = bib_getname()
        required(",")
    else:
        key = "<string>"
    entry["mykey"] = key
    lastsuccessfulkey = key
    nextfield = bib_getfield()
    while nextfield <> None:
        (fieldname,value) = nextfield
        entry[fieldname] = value
        expect(",")
        nextfield = bib_getfield()
    return (key,entry)

# Load bib file and return a dictionary with for each key a dictionary
# of all the fields for that record;
#
# note: the key "mytype" holds the type of entry, the key "mykey" 
def bib_parse(file,log):
    global lastsuccessfulkey
    log.write("Processing %s: " % file)
    entries = {} 
    try:
        initch( file )
    except BibError:
        log.write(" does not exist. Skipped.\n")
        return entries
    nextentry = bib_getentry()
    while nextentry <> None:
        (key,entry) = nextentry
        #log.write("%s\n"%key)
        entries[key] = entry
        expect("}")
        try:
            nextentry = bib_getentry()
        except BibError, err:
            log.write(str(err))
            return entries
    if nextentry <> None:
        log.write(" %s" % lastsuccessfulkey)
    else:
	log.write(" %d\n" % len(entries))
    return entries

def bib_write(f,record):
    f.write("@" + record['mytype'] + "{" + record['mykey'] + ",\n")
    keys = record.keys()
    keys.remove("mytype")
    keys.remove("mykey")
    for k in keys:
        f.write('\t' + k + ' = ' + record[k] + ',\n')
    f.write("}\n")
