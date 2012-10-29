#! /usr/bin/env python
# Original code by Adriaan de Groot. 
#
# Disributed under the BSD license
#
# Extract only those entries from a set of bibtex files that are cited in
# a latex document, and write those to standard output.
#
# usage: pybcompact  <latexfile> <bibtexfiles...>

import sys, string, os, fnmatch
import pybaux,pybbib

def usage ():
    print "usage: pybcompact <latexfile> <bibtoplevel>"
    return

def error (msg):
    sys.stderr.write("\npybcompact: error: %s\n" % msg)
    sys.exit (1)
    return

def warning (msg):
    sys.stderr.write("pybcompact: warning: %s\n" % msg)
    return

def collate (bibs,cites):
    found = []
    crossref = {}
    for c in cites:
        if bibs.has_key(c):
            useentry = merged_bibs[c]
            found.append(c)
            if useentry.has_key("crossref"):
                xref = useentry["crossref"]
                xref = xref.strip()
                xref = xref.strip("{}")
                xref = xref.strip("}{")
                crossref[xref] = 1
        else:
            warning("Not found: %s" % (c))
    return ( found,crossref.keys() )

# test input arguments
if len (sys.argv) < 3:
    usage ()
    sys.exit (1)

# get arguments
latexfile  = sys.argv [1]
bibdir = sys.argv [2]

# obtain citation keys from latex aux file
try:
    citations = pybaux.aux_citations(latexfile)
except pybaux.AuxError, err:
    error ('%s' % err)

# ensure citation keys unicity
tmp = {}
for c in citations:
    tmp [c] = 1
citations = tmp.keys ()

# is there something to do ?
if len (citations) == 0:
    sys.stderr.write("\npybcompact: no entries in aux file\n")
    sys.exit(0)

# load all bib files and merge in one big dictionary
merged_bibs = {}
bibfiles = []
pattern = '*.bib'

for root, dirs, files in os.walk(bibdir):
    for filename in fnmatch.filter(files, pattern):
        bibfiles.append(os.path.join(root, filename))

for bib in bibfiles:
    newbib = pybbib.bib_parse(bib,sys.stderr)
    for k in newbib.keys():
        merged_bibs[k] = newbib[k]

#
# lookup each citation in the databases and write it out
crossref = []
found = []
(found,crossref) = collate(merged_bibs,citations)
if len(crossref) > 0:
    sys.stderr.write("\nadding cross-references: ")
    sys.stderr.write(string.join(crossref,","))
    # collate(merged_bibs,crossref)

# Print crossrefs only at the end
for c in crossref:
    if c in found:
        sys.stderr.write("Leaving cross-reference " + c + " for later\n")
        found.remove(c)

# Print citations and mark them as found
for c in found:
    pybbib.bib_write(sys.stdout,merged_bibs[c])
    sys.stdout.write("\n")
    citations.remove(c)
for c in crossref:
    pybbib.bib_write(sys.stdout,merged_bibs[c])
    sys.stdout.write("\n")
    if c in citations:
        citations.remove(c)

# check if we were able to solve all the citations
if len (citations) > 0:
    warning ("can't find the following entries: %s"
           % string.join (citations, ", "))


print >>sys.stderr, "\n";
# Local Variables:
# mode: python
# End:
