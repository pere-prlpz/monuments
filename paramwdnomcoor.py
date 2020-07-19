# Actualitza les llistes com com paramwd.py
# a partir del nom (paràmetre nomcoor de la llista) buscant-lo als àlies en català.
# Funciona amb elements acabats de crear amb llistamon.py, que posa nomcoor com
# a àlies.
# Pensat pels monuments menorquins i valencians que no tenen un codi
# (o no tenen un codi prou fiable com per pujar-lo a Wikidata).
# Substitueix paramwdnom.py que feia servir el nom i estava pensar per Barcelona.
# Se li ha d'indicar la llista i el nom.
# Exemple:
# python paramwdnomcoor.py llista de monuments de Ferreries -menorca
# Les cometes són opcionals.
# -menorca: busca entre els monuments de Menorca

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

def get_alies(qlloc, verbose=False):
    # llocs de Wikidata situats al destí
    estats = ["Q228", "Q29"]
    if qlloc in estats:
        query="""SELECT DISTINCT ?cosa ?alies
        WHERE {
            ?cosa wdt:P17 wd:"""+qlloc+""".
            ?cosa skos:altLabel ?alies.
            FILTER(lang(?alies)="ca")
        }"""
    else:
        query = """SELECT DISTINCT ?cosa ?alies
        WHERE {
            ?cosa wdt:P131* wd:"""+qlloc+""".
            ?cosa skos:altLabel ?alies.
            FILTER(lang(?alies)="ca")
        }"""
    if verbose:
        print(query)
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
arguments = sys.argv[1:]
diccllocs = {"menorca":"Q52636", "pval":"Q5720", "and":"Q228"}
lloc = ""
if len(arguments)>0:
    for unlloc in diccllocs.keys():
        if "-"+unlloc in arguments:
            lloc=diccllocs[unlloc]
            arguments.remove("-"+unlloc)
if lloc=="":
    lloc=diccllocs["pval"]
verbose=False
if "-verbose" in arguments:
    verbose=True
    arguments.remove("-verbose")
if len(arguments)>0:
    nomllista=" ".join(arguments)
else:
    print("Manca el nom de la llista de monuments. Agafem opció per defecte")
    nomllista="Llista de monuments des Castell"
print ("Important monuments existents de Wikidata")
dicnoms = get_alies(lloc, verbose=verbose)
site=pwb.Site('ca')
pag = pwb.Page(site, nomllista)
print (pag)
actuallista(pag, dicnoms)