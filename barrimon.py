#-*- coding: utf-8 -*-
#
# Script per pujar barri o districte dels monuments a partir de les llistes

import pywikibot as pwb
from pywikibot import pagegenerators
from SPARQLWrapper import SPARQLWrapper, JSON
from collections import Counter
import math
import re
import pickle
import sys
import urllib
import time
from urllib.parse import unquote

def treuparams(plant):
  params = {}
  for i in range(len(plant[1])):
    trossos=plant[1][i].split("=")
    #print (trossos)
    params[trossos[0]]="=".join(trossos[1:])
  return(params)

def monunallista(llista, i0=1, site=pwb.Site('ca')):
# Retorna diccionari amb els monuments d'una llista de monuments
# i una llista amb els paràmetres wikidata.
# Fa servir el paràmetre wikidata com a clau.
# Els que no en tenen els dóna un índex provisional.
# Al diccionari sobreescriu els duplicats.
    fileraIPA=pwb.Page(site, "Plantilla:Filera IPA")
    fileraBIC=pwb.Page(site, "Plantilla:Filera BIC")
    fileraBICval=pwb.Page(site, "Plantilla:Filera BIC Val")
    fileraBICand=pwb.Page(site, "Plantilla:Filera BIC And")
    fileraMH=pwb.Page(site, "Plantilla:Filera MH")
    fileraBCsard=pwb.Page(site, "Plantilla:Filera BC Sard")
    fileraArt=pwb.Page(site, "Plantilla:Filera art públic")
    fileres=[fileraIPA, fileraBIC, fileraBICval, fileraBICand, fileraMH, fileraBCsard, fileraArt]
    plantilles = llista.templatesWithParams()
    monllista = {}
    monq = []
    monnoq = []
    ni = i0
    cat0=""
    for plantilla in plantilles:
      #print(plantilla[0])
      if plantilla[0] in fileres:
        params=treuparams(plantilla)
        if "wikidata" in params.keys() and len(params["wikidata"])>2:
            index=params["wikidata"]
            monq.append(index)
        else:
            index="NWD"+str(ni)
            ni=ni+1
            monnoq.append(index)
        monllista[index]=params
        if cat0=="":
            if plantilla[0]==fileraIPA:
                cat0="ipac"
            elif plantilla[0]==fileraBICval:
                cat0="igpcv"
            elif plantilla[0]==fileraBIC:
                cat0="bic"
            elif plantilla[0]==fileraBICand:
                cat0="and"
            elif plantilla[0]==fileraMH:
                cat0="mh"
            elif plantilla[0]==fileraBCsard:
                cat0="sard"
    return(monllista, monq, monnoq, cat0)

# CREC QUE NO CAL
def monllistes(nomorigen, site=pwb.Site('ca')):
    if re.match("llistes", nomorigen.casefold()):
        cat = pwb.Category(site,'Category:'+nomorigen)
        print(cat)
        llistes = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
    else:
        llistes = [pwb.Page(site, nomorigen)]
    monllistes = {}
    monqs = []
    monnoqs = []
    n = 1
    cataleg=""
    for llista in llistes:
        print(llista)
        monllista1, llistaq1, faltenq1, cat1 =monunallista(llista, site=site, i0=n)
        #print(monllista1)#
        n=n+len(faltenq1)
        monllistes.update(monllista1)
        monqs = monqs + llistaq1
        monnoqs = monnoqs + faltenq1
        if cataleg=="":
            cataleg = cat1
    #print(monllistes)#
    return (monllistes, monqs, monnoqs, cataleg)

def get_results(endpoint_url, query):
    user_agent = "PereBot/1.0 (ca:User:Pere_prlpz; prlpzb@gmail.com) Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

def carrega_monwd(qitems, qtipusmun="Q2074737", mostra=False):
    n = len(qitems)
    print(n,"elements per carregar")
    if n<150:
        inicis=[0]
        finals=[n]
    else:
        numtrossos=round(n/100)
        midatros=round(n/numtrossos)
        inicis=[i*midatros for i in range(0,numtrossos)]
        finals=inicis[1:]+[n]
    monuments={}
    for i in range(len(inicis)):
        print("carregant lot",i)
        monuments.update(get_monwd(qitems[inicis[i]:finals[i]], qtipusmun, mostra))
    print(len(monuments), "monuments llegits en", len(inicis),"fases")
    return(monuments)

def get_monwd(qitems, qtipusmun="Q2074737", mostra=False):
    # Llegeix amb una query dades d'una llista de monuments a Wikidata.
    # qtipusmun és el q del tipus de municipi (per defecte municipi d'Espanya)
    #print(qitems)
    query = """SELECT DISTINCT ?item ?lon ?lat ?imatge ?prot ?itemLabel ?protLabel 
    ?ipac ?bic ?igpcv ?sipca ?merimee ?ajbcn
    ?mun ?estil ?estilLabel ?ccat ?commonslink ?estat ?conserva ?inst ?instLabel
    WHERE {
      hint:Query hint:optimizer "None".
      VALUES ?item {"""+" ".join(["wd:"+el for el in qitems])+"""}
      OPTIONAL {
        ?item wdt:P625 ?coord.
      ?item p:P625 ?coordinate .
      ?coordinate psv:P625 ?coordinate_node .
      ?coordinate_node wikibase:geoLatitude ?lat .
      ?coordinate_node wikibase:geoLongitude ?lon .
    }
      OPTIONAL {?item wdt:P18 ?imatge}
      OPTIONAL {?item wdt:P131 ?adm}
      OPTIONAL {?item wdt:P1435 ?prot}
      OPTIONAL {?item wdt:P373 ?ccat}
      OPTIONAL {?item wdt:P1600 ?ipac}
      OPTIONAL {?item wdt:P808 ?bic}
      OPTIONAL {?item wdt:P2473 ?igpcv}
      OPTIONAL {?item wdt:P3580 ?sipca}
      OPTIONAL {?item wdt:P380 ?merimee}
      OPTIONAL {?item wdt:P11557 ?ajbcn}
      OPTIONAL {
       ?item wdt:P131* ?mun.
       ?mun wdt:P31/wdt:P279* wd:"""+qtipusmun+""".
      }
      OPTIONAL {?item wdt:P149 ?estil}
      OPTIONAL {?item wdt:P31 ?inst}
      OPTIONAL {?commonslink schema:about ?item;
         schema:isPartOf <https://commons.wikimedia.org/> }
      OPTIONAL {?item wdt:P17 ?estat}
      OPTIONAL {?item wdt:P5816 ?conserva}
    SERVICE wikibase:label {
    bd:serviceParam wikibase:language "ca" .
    }
    }"""
    if mostra: print(query)
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    mons={}
    for mon in results["results"]["bindings"]:
        if "item" in mon.keys():
            qitem=mon["item"]["value"].replace("http://www.wikidata.org/entity/","")
            mons[qitem]=mon
    return(mons)

def get_monbarris(mostra=False):
    query ="""# monuments de Barcelona amb barri
SELECT DISTINCT ?item ?itemLabel  ?barri ?barriLabel WHERE {
  ?item wdt:P1435 [].
    ?item wdt:P131+ ?barri.
    ?barri wdt:P31 wd:Q75135432.
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "[AUTO_LANGUAGE],ca,en,es,fr,de" . 
  }
}
    """
    if mostra: print(query)
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    mons={}
    for mon in results["results"]["bindings"]:
        if "item" in mon.keys():
            qitem=mon["item"]["value"].replace("http://www.wikidata.org/entity/","")
            mons[qitem]=mon
    return(mons)

def get_mondistrictes(mostra=False):
    query ="""# monuments de Barcelona segons el districte 
SELECT DISTINCT ?item ?itemLabel  ?districte ?districteLabel WHERE {
  ?item wdt:P1435 [].
    ?item wdt:P131+ ?districte.
    ?districte wdt:P31 wd:Q790344.
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "[AUTO_LANGUAGE],ca,en,es,fr,de" . 
  }
}
    """
    if mostra: print(query)
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    mons={}
    for mon in results["results"]["bindings"]:
        if "item" in mon.keys():
            qitem=mon["item"]["value"].replace("http://www.wikidata.org/entity/","")
            mons[qitem]=mon
    return(mons)

def get_llocsllistes(mostra=False):
    query ="""# llistes de llocs de Barcelona
SELECT ?llista ?llistaLabel ?lloc ?llocLabel ?article WHERE {
  ?llista wdt:P31 wd:Q13406463.
  ?llista p:P360 ?statement.
  ?statement pq:P131 ?lloc.
  ?lloc wdt:P131+ wd:Q1492.
  ?article schema:about ?llista.
  ?article schema:isPartOf <https://ca.wikipedia.org/>.
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "[AUTO_LANGUAGE],ca,en,es,fr,de" . 
  }
}
    """
    if mostra: print(query)
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    mons={}
    for mon in results["results"]["bindings"]:
        if "llista" in mon.keys():
            qitem=mon["llista"]["value"].replace("http://www.wikidata.org/entity/","")
            mons[qitem]=mon
    return(mons)

def get_per_inst(inst, mostra=False):
    query ="""# coses per instància
SELECT ?item ?itemLabel WHERE {
  ?item wdt:P31 wd:"""+inst+""".
SERVICE wikibase:label {
    bd:serviceParam wikibase:language "[AUTO_LANGUAGE],ca,en,es,fr,de" . 
  }
}
    """
    if mostra: print(query)
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    mons={}
    for mon in results["results"]["bindings"]:
        if "item" in mon.keys():
            qitem=mon["item"]["value"].replace("http://www.wikidata.org/entity/","")
            mons[qitem]=mon
    return(mons)


# el programa comença aquí
site=pwb.Site('ca')
monbarris= get_monbarris()
#print(monbarris)
print("monbarris:",len(monbarris))
mondistr= get_mondistrictes()
#print(mondistr)
print("mondistr:",len(mondistr))
llocsllistes=get_llocsllistes()
print("llocsllistes:",len(llocsllistes))
#print(llocsllistes)
llocllista = {}
for llista in llocsllistes:
    #print(llista)
    nomllista = llocsllistes[llista]["article"]["value"]
    nomllista = unquote(nomllista)
    nomllista = nomllista.replace("https://ca.wikipedia.org/wiki/","")
    nomllista = nomllista.replace("_"," ")
    qlloc = llocsllistes[llista]["lloc"]["value"].replace("http://www.wikidata.org/entity/","")
    llocllista[nomllista]=qlloc
#print(llocllista)
barris = get_per_inst("Q75135432")
#print(barris)
districtes = get_per_inst("Q790344")
#print(districtes)
instruccions = ""
for nomLlista in llocllista:
    #print(nomLlista)
    if llocllista[nomLlista] in districtes:
        districte=llocllista[nomLlista]
    else:
        districte=False
    if llocllista[nomLlista] in barris:
        barri=llocllista[nomLlista]
    else:
        barri=False
    print(nomLlista, barri, districte)
    #posadivisio(nomLlista, barri, districte)
    pagllista = pwb.Page(site, nomLlista)
    monllista, llistaq, faltenq, cat =monunallista(pagllista)
    #print(monllista)
    print("monllista:",len(monllista))
    for qmon in llistaq:
        if barri and not qmon in monbarris:
            print("posar barri", barri, "a", qmon)
            instruccio = qmon+"|"+"P131"+"|"+ barri + "|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
        elif districte and not qmon in mondistr:
            print("posar districte", districte, "a", qmon)
            instruccio = qmon+"|"+"P131"+"|"+ districte + "|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
print("Instruccions pel quickstatements:")
print(instruccions,"\n")

        