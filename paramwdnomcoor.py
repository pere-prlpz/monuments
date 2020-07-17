# Actualitza les llistes com com paramwd.py
# però és pels monuments de les llistes de Barcelona que no tenen codi IPAC

import pywikibot as pwb
from SPARQLWrapper import SPARQLWrapper, JSON
import mwparserfromhell
#from collections import Counter
#import math
import re
import pickle
import sys
import time
import urllib

def get_results(endpoint_url, query):
    user_agent = "PereBot/1.0 (ca:User:Pere_prlpz; prlpzb@gmail.com) Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

def get_alies(lloc="menorca"):
    # llocs de Wikidata situats al destí
    diccllocs = {"menorca":"Q52636"}
    if lloc in diccllocs:
        qlloc=diccllocs[lloc]
    else:
        print("Lloc no previst")
        return({})
    query = """SELECT DISTINCT ?cosa ?alies
    WHERE {
        ?cosa wdt:P131* wd:"""+qlloc+""".
        ?cosa skos:altLabel ?alies.
        FILTER(lang(?alies)="ca")
    }"""
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    dicipac={}
    for mon in results["results"]["bindings"]:
        qmon=mon["cosa"]["value"].replace("http://www.wikidata.org/entity/","")
        dicipac[mon["alies"]["value"]]=qmon
    return(dicipac)

def actuallista(pllista,diccipa,pagprova=False):
    resultat=u""
    origen=pllista.title()
    text=pllista.get()
    text0=text
    code = mwparserfromhell.parse(text)
    t=code.filter_templates();
    #print(t)
    for template in t:
        #print (template.name)
        if template.has("wikidata"):
            wd=template.get("wikidata").value.strip()
            wd=re.sub("<!-- no ?[Ww][Dd] ?auto -->", "", wd)
            #print(wd)
        else:
            wd=""
        if wd=="" and template.has("nomcoor"):
            nombusca = template.get("nomcoor").value.strip()
            print("Busquem",template.get("nomcoor").value.strip())
            if nombusca in diccipa.keys():
                print(diccipa[nombusca])
                wdposar=diccipa[nombusca]
                #print(wdposar)
                template.add("wikidata",wdposar)
            else:
                print("Inexistent")
    text=code
    if text != text0:
        print("Desant",pllista)
        pllista.put(text,u"Robot actualitza el paràmetre wikidata a partir dels noms dels monuments")
    else:
        print("Cap canvi")
    return()

# el programa comença aquí
lloc="menorca"
arguments = sys.argv[1:]
if len(arguments)>0:
    if "-menorca" in arguments:
        lloc="menorca"
        arguments.remove("-menorca")
if len(arguments)>0:
    nomllista=" ".join(arguments)
else:
    print("Manca el nom de la llista de monuments. Agafem opció per defecte")
    nomllista="Llista de monuments des Castell"
print ("Important monuments existents de Wikidata")
dicnoms = get_alies(lloc)
site=pwb.Site('ca')
pag = pwb.Page(site, nomllista)
print (pag)
actuallista(pag, dicnoms)