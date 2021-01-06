#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on 17/12/2020

@author: bham

Helper script to count sylls from zettels
for getting Flesch-Kincaid score. Adapted
from: https://spacy.io/universe/project/spacy_syllables/

"""
import spacy, sys, re
from spacy_syllables import SpacySyllables
from nltk.corpus import cmudict # because Spacy/Pyphen syllable count inaccurate sometimes.
from functools import lru_cache

cm = cmudict.dict()
data = []

def filterOthers(contents):
    """"
    To get rid of oft used markup stuff.
    """

    # Headers/sub-headers in markup
    z = re.compile('(?P<headings>^#+[\w\s,\.]+\\n$)|' +\
                   '(?P<emphs>\*{1,2})|' +\
                   # '(?P<links>\([\w\s#]*\[\[\d{12,18}\]\]\s+pp\..+\))|' + \
                   '(?P<links>\([\w\s#]*\[\[\d{12,18}\]\]\s+.+\))|' +\
                   '(?P<tags>(?<!\(\s)#\w+(?!\s+\[\[))|' +\
                   '(?P<citations>\[@[\w\d]+\](?!:))|' +\
                   '(?P<footnote>\[\^\d+\])|' +\
                   '(?P<indents>^\s+(?=-[\s\w\W]+\\n$))|' +\
                   '(?P<footnotes>^\[\d+\][\s\w]+.*\\n|^\[\d+\].*\d{12,18}\]\]\s+.*\\n)|' +\
                   '(?P<references>^<!-{2}\sreferences\s\(auto\)\\n$)|' +\
                   '(?P<reference>^\[@[\w\d]+\]:\s+.*\\n$)|' +\
                   '(?P<other>-{1,2}>\s+)|' +\
                   '(?P<misc>-{4})|' +\
                   '(?P<referen>^-{2}>\\n$)',
                   re.IGNORECASE|re.UNICODE|re.MULTILINE)

    newContents = ''

    for n in contents:
        if n != '\n':
            a = re.sub(z, '', n)
            newContents += re.sub(r'\n', ' ', a)

    return (newContents)

def filterTempl(x):
    """
    Zettel template removal.
    Zettel template defined in sublime_zk user config file.
    """
    if x[0].strip('\n') == '---':
        if x[len(x)-1].strip('\n') == '----':
            contents = x[8:len(x)-2]
        else:
            contents = x[8:]
    elif x[len(x)-1].strip('\n') == '----':
        contents = x[:len(x)-2]
    else:
        contents = x
    return(contents)

def check_cmu(j):
    try:
        return([len(list(y for y in x if y[-1].isdigit())) for x in cm[j.lower()]])
    except:
        return([0])

@lru_cache()
def getRes(doc):
    p,h,b,replaced = 0,0,0,0
    for token in doc:
        try:
            if token._.syllables_count >= check_cmu(token.text)[0]:
                data.append((token.text, token._.syllables, token._.syllables_count))
            else:
                data.append((token.text, token._.syllables, check_cmu(token.text)[0]))
                replaced += 1
        except:
            data.append((token.text, token._.syllables, token._.syllables_count))

    for m,_,n in data:
        if m == '.': b+=1
        if not isinstance(n, type(None)):
            p+=n
            h+=1
    return(dict(data=data,
                syllables=p,
                words=h,
                sentences=b,
                replaced=replaced))

def fk_score(p,h,b):
    try:
        return(206.835-(1.015*(h/b))-(84.6*(p/h)))
    except ZeroDivisionError:
        return(206.835-(1.015*(h/1))-(84.6*(p/h)))

with open(sys.argv[2], mode='rt') as f:
    d = f.readlines()
    #print(d)
    contents = filterOthers(filterTempl(d))

nlp = spacy.load('en_core_web_lg') # https://spacy.io/models/en
syllables = SpacySyllables(nlp)
nlp.add_pipe(syllables, after='tagger')
doc = nlp(contents)
vals = getRes(doc)

if __name__ == '__main__':
    if sys.argv[1] == '--fkonly':
        print('{}'.format(str(round(fk_score(vals['syllables'],
                                                   vals['words'],
                                                   vals['sentences']),2))))
    else:
        print('Used cmudict: {}'.format(str(vals['replaced'])))
        print('Total syllables: {}'.format(str(vals['syllables'])))
        print('Total words: {}'.format(str(vals['words'])))
        print('Total sentences: {}'.format(str(vals['sentences'])))
        print('FK score: {}'.format(str(round(fk_score(vals['syllables'],
                                                   vals['words'],
                                                   vals['sentences']),2))))

    #with open('/tmp/res_sylls_text', mode='w') as f:
    #    f.write(contents)
else:
    #sys.stdout.write('[p, h, b]\n')
    #sys.stdout.flush()
    sys.exit(0)
