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

def get_monwd(qitems):
    query = """SELECT DISTINCT ?item ?lon ?lat ?imatge ?prot ?itemLabel ?protLabel ?ipac ?mun ?estil ?estilLabel ?ccat ?commonslink ?estat ?conserva ?inst ?instLabel
    WHERE {
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
      OPTIONAL {
       ?item wdt:P131* ?mun.
       ?mun wdt:P31 wd:Q33146843.
      }
      OPTIONAL {?item wdt:P149 ?estil}
      OPTIONAL {?item wdt:P31 ?inst}
      OPTIONAL {?commonslink schema:about ?item;
         schema:isPartOf <https://commons.wikimedia.org/> }
      OPTIONAL {?item wdt:P17 ?estat}
      OPTIONAL {?item wdt:P5816 ?conserva}
    SERVICE wikibase:label {
    bd:serviceParam wikibase:language "ca,en,oc,fr,es" .
    }
    }"""
    #print(query)
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    mons={}
    for mon in results["results"]["bindings"]:
        if "item" in mon.keys():
            qitem=mon["item"]["value"].replace("http://www.wikidata.org/entity/","")
            mons[qitem]=mon
    return(mons)

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
        if template.name.matches(("Filera IPA")):
            if template.has("wikidata"):
                wd=template.get("wikidata").value.strip()
                wd=re.sub("<!-- no ([Ww][Dd] )?((auto|amb bot) )?-->", "", wd)
                #print(wd)
            else:
                wd=""
            if wd=="" and template.has("id"):
                id=template.get("id").value.strip()
                id=re.sub("IPA-","",id)
                print("Per",template.get("nomcoor").value.strip(),"busquem id:", id)
                if id in diccipa.keys():
                    print(diccipa[id])
                    wdposar=diccipa[id]["qmon"]
                    #print(wdposar)
                    template.add("wikidata",wdposar)
                else:
                    print("Inexistent")
    text=code
    if text != text0:
        print("Desant",pllista)
        pllista.put(text,u"Robot actualitza el paràmetre wikidata a partir del codi IPAC")
    else:
        print("Cap canvi")
    return()



# el programa comença aquí
ipacdisc=False
arguments = sys.argv[1:]
if len(arguments)>0:
    if "-ipacdisc" in arguments:
        ipacdisc=True
        arguments.remove("-ipacdisc")
if len(arguments)>0:
    nomllista=" ".join(arguments)
else:
    print("Manca el nom de la llista de monuments. Agafem opció per defecte")
    nomllista="Llista de monuments de l'Eixample de Barcelona"
print ("Important IPAC existents de Wikidata")
ipacexist=carrega_ipac(ipacdisc)
site=pwb.Site('ca')
pag = pwb.Page(site, nomllista)
#pag = pwb.Page(site, "Usuari:PereBot/taller")
print (pag)
actuallista(pag, ipacexist)