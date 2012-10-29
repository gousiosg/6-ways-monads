# Original code by Adriaan de Groot. 
#
# Disributed under the BSD license
#
# Functions to parse TeX/LaTeX aux files

import os, re, string

# regular expression to match in the .aux file
citation_re = re.compile ('\\citation\{([^\}]+)\}')
include_re  = re.compile ('^\\\@input\{([^\}]+)\}')

# report errors by throwing this exception
class AuxError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


# Open an .aux file and retrun it's file handle
def aux_open(file):
    auxname = os.path.splitext (file) [0] + '.aux'
    try:
        auxf = open (auxname, 'r')
    except IOError, err:
        raise AuxError, '%s: %s' % (auxname, err)
    return auxf

# Readin and expand .aux file, returning a list of all lines in the auxfile and
# all .aux files it references
def aux_lines(file):
    auxf = aux_open(file)
    lines = [] 
    # parse the whole file
    for line in auxf.readlines():
        line = string.strip (line)
        lines.append(line)
        # we have to enter an additional .aux file
        match = include_re.search (line)
        if match:
            lines = lines + aux_lines (match.group (1))
    auxf.close ()
    return lines

# Extract citation keys from the (expanded) .aux file and return as list
def aux_citations(file):
    citations = []
    for line in aux_lines(file):
        # we match a new citation
        match = citation_re.search (line)
        if match:
            references = match.group(1)
            for k in references.split(","):
                citations.append (k.strip())
    return citations

