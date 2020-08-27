# Busca a Wikidata elements de monuments que falti enllaça en una llista de monuments i actualitza el paràmetre wikidata a la llista.
# Comprova si algun paràmetre wikidata apunta a una redirecció i el susbstitueix pel seu destí.
# La llista o categoria de llistes se li dóna com a paràmetre extern. Per exemple:
# python paramwd.py "Llista de monuments de Viladrau"
# python paramwd.py "Llistes de monuments del País Valencià"
# Les cometes són opcionals.
# Paràmetres:
# -iddisc No carrega els monuments de Wikidata sinó del disc. 

import pywikibot as pwb
from pywikibot import pagegenerators
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

def get_results2(endpoint_url, query):
    #user_agent = "PereBot/1.0 (ca:User:Pere_prlpz) Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    user_agent = "PereBot/1.0 (ca:User:Pere_prlpz; prlpzb@gmail.com) Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    print (user_agent)
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    try:
        resposta = sparql.query().convert()
        return resposta
    except urllib.error.HTTPError:
        print("Error HTTP. Espero i ho torno a provar.")
        time.sleep(15)
        resposta = sparql.query().convert()
        return resposta
        
def get_ipac(desa=True):
    # monuments existents amb codi IPAC
    query = """SELECT DISTINCT ?mon ?monLabel ?ipac
    WHERE {
      ?mon wdt:P1600 ?ipac.
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "ca, en".
      }
    }"""
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    dicipac={}
    for mon in results["results"]["bindings"]:
        qmon=mon["mon"]["value"].replace("http://www.wikidata.org/entity/","")
        nommon=mon["monLabel"]["value"]
        dicipac[mon["ipac"]["value"]]={"qmon":qmon, "nommon":nommon}
    if desa:
        fitxer = r"C:\Users\Pere\Documents\perebot\ipac.pkl"
        pickle.dump(dicipac, open(fitxer, "wb"))
    return(dicipac)

def carrega_ipac(disc=False):
    if disc==True:
        print ("Llegint del disc els IPAC existents a Wikidata")
        ipac = pickle.load(open(r"C:\Users\Pere\Documents\perebot\ipac.pkl", "rb"))
    else:
        print ("Important amb una query els IPAC existents a Wikidata")
        ipac = get_ipac()
    return (ipac)

def get_igpcv(desa=True):
    # monuments existents amb codi igpcv
    query = """SELECT DISTINCT ?mon ?monLabel ?id
    WHERE {
      ?mon wdt:P2473 ?id.
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "ca, en".
      }
    }"""
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    dicigpcv={}
    for mon in results["results"]["bindings"]:
        qmon=mon["mon"]["value"].replace("http://www.wikidata.org/entity/","")
        nommon=mon["monLabel"]["value"]
        dicigpcv[mon["id"]["value"]]={"qmon":qmon, "nommon":nommon}
    if desa:
        fitxer = r"C:\Users\Pere\Documents\perebot\igpcv.pkl"
        pickle.dump(dicigpcv, open(fitxer, "wb"))
    return(dicigpcv)

def carrega_igpcv(disc=False):
    if disc==True:
        print ("Llegint del disc els igpcv existents a Wikidata")
        igpcv = pickle.load(open(r"C:\Users\Pere\Documents\perebot\igpcv.pkl", "rb"))
    else:
        print ("Important amb una query els igpcv existents a Wikidata")
        igpcv = get_igpcv()
    return (igpcv)

def get_sipca(desa=True):
    # monuments existents amb codi sipca
    query = """SELECT DISTINCT ?mon ?monLabel ?id
    WHERE {
      ?mon wdt:P3580 ?id.
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "ca, en".
      }
    }"""
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    dicid={}
    for mon in results["results"]["bindings"]:
        qmon=mon["mon"]["value"].replace("http://www.wikidata.org/entity/","")
        nommon=mon["monLabel"]["value"]
        dicid[mon["id"]["value"]]={"qmon":qmon, "nommon":nommon}
    if desa:
        fitxer = r"C:\Users\Pere\Documents\perebot\sipca.pkl"
        pickle.dump(dicid, open(fitxer, "wb"))
    return(dicid)

def carrega_sipca(disc=False):
    if disc==True:
        print ("Llegint del disc els sipca existents a Wikidata")
        sipca = pickle.load(open(r"C:\Users\Pere\Documents\perebot\sipca.pkl", "rb"))
    else:
        print ("Important amb una query els sipca existents a Wikidata")
        sipca = get_sipca()
    return (sipca)

def get_bic(desa=True):
    # monuments existents amb codi igpcv
    query = """SELECT DISTINCT ?mon ?monLabel ?id
    WHERE {
      ?mon wdt:P808 ?id.
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "ca, es, en".
      }
    }"""
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    dicbic={}
    for mon in results["results"]["bindings"]:
        qmon=mon["mon"]["value"].replace("http://www.wikidata.org/entity/","")
        nommon=mon["monLabel"]["value"]
        dicbic[mon["id"]["value"]]={"qmon":qmon, "nommon":nommon}
    if desa:
        fitxer = r"C:\Users\Pere\Documents\perebot\bic.pkl"
        pickle.dump(dicbic, open(fitxer, "wb"))
    return(dicbic)

def carrega_bic(disc=False):
    if disc==True:
        print ("Llegint del disc els BIC existents a Wikidata")
        bic = pickle.load(open(r"C:\Users\Pere\Documents\perebot\bic.pkl", "rb"))
    else:
        print ("Important amb una query els bic existents a Wikidata")
        bic = get_bic()
    return (bic)

def get_merimee(desa=True):
    # monuments existents amb codi Mérimée
    query = """SELECT DISTINCT ?mon ?monLabel ?id
    WHERE {
      ?mon wdt:P380 ?id.
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "ca, fr, en".
      }
    }"""
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    dicbic={}
    for mon in results["results"]["bindings"]:
        qmon=mon["mon"]["value"].replace("http://www.wikidata.org/entity/","")
        nommon=mon["monLabel"]["value"]
        dicbic[mon["id"]["value"]]={"qmon":qmon, "nommon":nommon}
    if desa:
        fitxer = r"C:\Users\Pere\Documents\perebot\merimee.pkl"
        pickle.dump(dicbic, open(fitxer, "wb"))
    return(dicbic)

def carrega_merimee(disc=False):
    if disc==True:
        print ("Llegint del disc els Mérimée existents a Wikidata")
        base = pickle.load(open(r"C:\Users\Pere\Documents\perebot\merimee.pkl", "rb"))
    else:
        print ("Important amb una query els Mérimée existents a Wikidata")
        base = get_merimee()
    return (base)

def qmon(dicc):
    mon = [x["qmon"] for x in list(dicc.values())]
    return (mon)

def actuallista(pllista, diccipa, diccigpcv, diccbic, diccsipca, diccmerimee, existents, pagprova=False):
    resultat=u""
    origen=pllista.title()
    text=pllista.get()
    text0=text
    code = mwparserfromhell.parse(text)
    t=code.filter_templates();
    #print(t)
    codiclau = []
    sumariredir = ""
    for template in t:
        #print (template.name)
        posat = False
        if template.has("wikidata"):
            wd=template.get("wikidata").value.strip()
            wd=re.sub("<!-- no ([Ww][Dd] )?((auto|amb bot) )?-->", "", wd)
            #print(wd)
        else:
            wd=""
        if wd !="":
            if wd in existents:
                #print (wd, "conegut")
                pass
            else:
                item = pwb.ItemPage(repo, wd)
                if item.isRedirectPage():
                    wdposar=item.getRedirectTarget().title()
                    template.add("wikidata",wdposar)
                    print (wd, "redirecció a", wdposar)
                    sumariredir = "arregla redireccions a Wikidata"
                else:
                    print ("comprovat que", wd, "no és una redirecció")        
        if template.name.matches(("filera IPA")):
           if wd=="" and template.has("id"):
                id=template.get("id").value.strip()
                id=re.sub("IPA-","",id)
                print("Per",template.get("nomcoor").value.strip(),"busquem id:", id)
                if id in diccipa.keys():
                    print(diccipa[id])
                    wdposar=diccipa[id]["qmon"]
                    #print(wdposar)
                    template.add("wikidata",wdposar)
                    posat = True
                    codiclau.append("IPAC")
                else:
                    print("IPAC inexistent")
        if template.name.matches(("filera BIC Val")):
           if wd=="" and template.has("bic"):
                id=template.get("bic").value.strip()
                print("Per",template.get("nomcoor").value.strip(),"busquem id:", id)
                if id in diccigpcv.keys():
                    print(diccigpcv[id])
                    wdposar=diccigpcv[id]["qmon"]
                    #print(wdposar)
                    template.add("wikidata",wdposar)
                    posat = True
                    codiclau.append("IGPCV")
                else:
                    print("IGPCV inexistent")
        if (template.name.matches(("filera BIC Val"))  or template.name.matches(("filera BIC"))) and posat==False:
           if wd=="" and template.has("bic"):
                id=template.get("bic").value.strip()
                print("Per",template.get("nomcoor").value.strip(),"busquem id:", id)
                if id in diccbic.keys():
                    print(diccbic[id])
                    wdposar=diccbic[id]["qmon"]
                    #print(wdposar)
                    template.add("wikidata",wdposar)
                    posat = True
                    codiclau.append("BIC")
                else:
                    print("BIC inexistent")
        if template.name.matches(("filera BIC")) and posat==False:
           if wd=="" and template.has("bic"):
                id=template.get("bic").value.strip()
                print("Per",template.get("nomcoor").value.strip(),"busquem id:", id)
                if id in diccsipca.keys():
                    print(diccsipca[id])
                    wdposar=diccsipca[id]["qmon"]
                    #print(wdposar)
                    template.add("wikidata",wdposar)
                    posat = True
                    codiclau.append("SIPCA")
                else:
                    print("SIPCA inexistent")
        if template.name.matches(("filera MH")) and posat==False:
           if wd=="" and template.has("id"):
                id=template.get("id").value.strip()
                print("Per",template.get("nomcoor").value.strip(),"busquem id:", id)
                if id in diccmerimee.keys():
                    print(diccmerimee[id])
                    wdposar=diccmerimee[id]["qmon"]
                    #print(wdposar)
                    template.add("wikidata",wdposar)
                    posat = True
                    codiclau.append("Mérimée")
                else:
                    print("Mérimée inexistent")
    text=code
    if text != text0:
        print("Desant",pllista)
        if len(codiclau)>0:
            claus = " i ".join(set(codiclau))
            sumarinous = "actualitza el paràmetre wikidata a partir del codi "+claus
        else:
            sumarinous = ""
        if len(sumarinous)*len(sumariredir)>0:
            conj = " i "
        else:
            conj = ""
        sumari = "Robot "+sumarinous+conj+sumariredir
        pllista.put(text,sumari)
    else:
        print("Cap canvi")
    return()

def actuallistes(nomorigen, diccipa, diccigpcv, diccbic, diccsipca, diccmerimee, existents, pagprova=False):
    if re.match("llistes", nomorigen.casefold()):
        cat = pwb.Category(site,'Category:'+nomorigen)
        print(cat)
        llistes = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
    else:
        llistes = [pwb.Page(site, nomorigen)]
    for llista in llistes:
        print(llista)
        actuallista(llista, diccipa, diccigpcv, diccbic, diccsipca, diccmerimee, existents, pagprova=False)
    return()

# el programa comença aquí
iddisc=False
arguments = sys.argv[1:]
if len(arguments)>0:
    if "-ipacdisc" in arguments:
        iddisc=True
        arguments.remove("-ipacdisc")
    if "-iddisc" in arguments:
        iddisc=True
        arguments.remove("-iddisc")
if len(arguments)>0:
    nomllista=" ".join(arguments)
else:
    print("Manca el nom de la llista de monuments. Agafem opció per defecte")
    nomllista="Llista de monuments de l'Eixample de Barcelona"
print ("Important codis existents de Wikidata")
ipacexist=carrega_ipac(iddisc)
igpcvexist=carrega_igpcv(iddisc)
bicexist=carrega_bic(iddisc)
sipcaexist=carrega_sipca(iddisc)
merimeeexist=carrega_merimee(iddisc)
claustot = qmon(ipacexist)+qmon(igpcvexist)+qmon(bicexist)+qmon(sipcaexist)+qmon(merimeeexist)
site=pwb.Site('ca')
repo = site.data_repository()
#pag = pwb.Page(site, nomllista)
#print (pag)
actuallistes(nomllista, ipacexist, igpcvexist, bicexist, sipcaexist, merimeeexist, claustot)