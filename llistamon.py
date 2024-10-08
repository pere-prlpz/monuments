#-*- coding: utf-8 -*-
#
# Funcions per llegir llistes de monuments i pujar a Wikidata les dades que faltin.
# Al final genera un informe de diferències i les instruccions pel quickstatements.
# Fa servir el paràmetre wikidata com a clau i crea items amb les fileres que no en tinguin.
# La llista o categoria de llistes se li dóna com a paràmetre extern. Per exemple:
# python llistamon.py "Llista de monuments de Viladrau"
# python llistamon.py "Llistes de monuments d'Osona"
# Les cometes són opcionals.
# Paràmetres generals:
# -nocrea: no crea items nous a Wikidata 
# -creatot: crea tots els elements que pugui, incloent els que no tinguin un codi vàlid per Wikidata
# -nocommons: no posa el sitelink de commons (útil quan algun ja està enllaçat a Wikidata i quickstatemens dóna error)
# -iddisc: no importa tots els item amb codi IPAC de Wikidata (P1600) o IGPCV sinó que fa servir la versió guardada el darrer cop.
# -verbose: més sensible a informar de diferències (menys diferència coordenades, estils amb id diferent que es diuen igual, etc.)
# -verbose1: encara més sensible que verbose. Dóna molta informació habitualment poc útil.
# Paràmetres per esborrar dades:
# El programa no esborra ni canvia propietats que ja estiguin a Wikidata excepte amb els següents paràmetres
# (utilitzeu-los amb prudència):
# -treubcil: treu P1435=BCIL de Wikidata quan a la llista són béns inventariats
# -posabcil: treu P1435=Inventariat de Wikidata quan a la llista són BCIL
# -treucoor: canvia certes coordenades existents a Wikidata per les de la llista. Només per suposats errors de datum amb esglésies.
# Abans de pujar un codi IGPCV comprova el codi amb el web de la Generalitat.
#
# PER FER:
# Millorar la desambiguació de municipis fent servir el parèntesis (bàsicament pels francesos).
# Adaptar-lo a plantilles de monuments l'Alguer.
# Adaptar-lo a patrimoni natural, arbres singulars i rellotges de sol
# Reconèixer quan sitecommons ja està agafat
# Reconèixer i pujar dos estils junts
# Refer funcions trobar codis existents, que són totes iguals
#
# MANCANCES CONEGUDES:
# Pot donar avís de valors diferents quan a Wikidata o a la llista hi ha dos valors (o n'agafa un o no l'entén).
# Quan ha d'importar de Wikidata els municipis existents, tendeix fallar per time-out. Provant un parell o tres de cops acaba sortint.
# (Importar municipis de Wikidata s'ha de fer poc sovint, només si s'han d'actualitzar).

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

def al(sn):
    #print(sn)
    sn0=sn[:]
    sn0=sn0.strip(" []")
    sn0=re.sub("[\[\]]","",sn0)
    sn1=sn0[:]
    #print(sn,sn0,sn1)
    sn1 = re.sub("^[Ee]l ","al ",sn1)
    sn1 = re.sub("^[Ee]s ","as ",sn1) #balear
    #print(sn,sn0,sn1)
    sn1 = re.sub("^[Ee]ls ","als ",sn1)
    sn1 = re.sub("^L'","a l'",sn1)
    sn1 = re.sub("^La ","a la ",sn1)
    sn1 = re.sub("^Les ","a les ",sn1)
    #print(sn,sn1)
    if sn1==sn0:
        sn1="a "+sn0
    #print(sn,sn0,sn1)
    return sn1

def de(sn):
    sn1=sn[:]
    sn1 = re.sub("^[Ee]l ","del ",sn1)
    sn1 = re.sub("^[Ee]ls ","dels ",sn1)
    if sn1==sn:
        sn1="de "+sn
    return sn1

def distgeo(lat1, lon1, lat2, lon2):
    #print(lat1, lon1, lat2, lon2)
    lar1 = math.pi/180*lat1
    lor1 = math.pi/180*lon1
    lar2 = math.pi/180*lat2
    lor2 = math.pi/180*lon2
    cAC=math.cos(math.pi/2-lar1)
    cAB=math.cos(math.pi/2-lar2)
    sAC=math.sin(math.pi/2-lar1)
    sAB=math.sin(math.pi/2-lar2)
    calfa=math.cos(lor2-lor1)
    cCB=cAC*cAB+sAC*sAB*calfa
    #print("cCB=cAC*cAB+sAC*sAB*calfa")
    #print(cCB,cAC,cAB,sAC,sAB,calfa)
    cCB=min(cCB, 1)
    return(math.acos(cCB)*6371)

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
    fileres=[fileraIPA, fileraBIC, fileraBICval, fileraBICand, fileraMH, fileraBCsard]
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

def igpcv_url(idurl):
    # Cerca el codi IGPCV a partir d'idurl, mirant al web de la Generalitat.
    # Basat en https://ca.wikipedia.org/wiki/Usuari:Vriullop/igpcv.py
    codi ="Error idurl"
    webigpcv = urllib.request.urlopen("http://eduwp.edu.gva.es/patrimonio-cultural/ficha-inmueble.php?id="+idurl)
    textfitxa = str(webigpcv.read(), 'utf_8')
    webigpcv.close()
    nofitxa = re.search('El inmueble no existe', textfitxa)
    if nofitxa:
        codi='No existeix'
    else:
        codisearch = re.search('Codi</dt>\s+<dd>(?P<aixo>.*)</dd>', textfitxa)
        if codisearch:
            codi = codisearch.group('aixo')
            if not re.search('^[0-9]+$', codi):
                    codiparts = codi.split(".")
                    if len(codiparts) == 3:
                        codisufix = codiparts[2].split("-")
                        codi = "%02d.%02d.%03d-%03d" % (int(codiparts[0]), int(codiparts[1]), int(codisufix[0]), int(codisufix[1]))
    return(codi)
 
def get_results(endpoint_url, query):
    user_agent = "PereBot/1.0 (ca:User:Pere_prlpz; prlpzb@gmail.com) Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

def get_results2(endpoint_url, query):
    user_agent = "PereBot/1.0 (prlpzb@gmail.com) Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
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
    
def get_municipis(desa=True):
    # diccionari de municipis a item, directe i invers
    # l'invers (label a item) en minúscules (casefold)
    # Fa servir també noms oficials i alies si no dupliquen un label.
    # Ara municipis d'Espanya.
    query = """#Municipis del nostre entorn, amb els noms alternatius separats
    SELECT DISTINCT ?mun ?munLabel ?oficial ?alias ?calink
        WHERE {
    VALUES ?tipus {wd:Q484170
     wd:Q2989454
     wd:Q20899166
     wd:Q22927548
     wd:Q22927616
    # wd:Q84598477
    # wd:Q84599126
     wd:Q2074737
    # wd:Q2276925
    # wd:Q3284867
    # wd:Q5055981
     wd:Q33146843
    # wd:Q55863584
     wd:Q61763947
     wd:Q24279
     wd:Q21869758}
      ?mun wdt:P31 ?tipus.
        OPTIONAL {?mun wdt:P1448 ?oficial}
        OPTIONAL {?mun skos:altLabel ?alias.
                 FILTER(lang(?alias)="ca")}
      OPTIONAL {?calink schema:about ?mun;
         schema:isPartOf <https://ca.wikipedia.org/> }
        SERVICE wikibase:label {
        bd:serviceParam wikibase:language "ca" .
        }
    }"""
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    dicdirecte={}
    dicinvers={}
    for mon in results["results"]["bindings"]:
        #print(mon)
        #print(mon["mun"]["value"], mon["munLabel"]["value"])
        qmun=mon["mun"]["value"].replace("http://www.wikidata.org/entity/","")
        nommun=mon["munLabel"]["value"]
        dicdirecte[qmun]=nommun
        if "calink" in mon.keys():
            calink = mon["calink"]["value"].replace("https://ca.wikipedia.org/wiki/","")
            dicinvers[calink.casefold()]=qmun
        if not(nommun.casefold() in dicinvers.keys()): 
            dicinvers[nommun.casefold()]=qmun
        if "oficial" in mon.keys():
            nomoficial=mon["oficial"]["value"]
            if not(nomoficial.casefold() in dicinvers.keys()): 
                dicinvers[nomoficial.casefold()]=qmun
        if "alias" in mon.keys():
            alies=mon["alias"]["value"]
            if len(alies)>1 and not(alies.casefold() in dicinvers.keys()):
                dicinvers[alies.casefold()]=qmun   
    # municipis de França amb el departament per desambiguar
    query="""SELECT ?mun ?munLabel ?depLabel
    WHERE {
      hint:Query hint:optimizer "None".  
      ?mun wdt:P31 wd:Q484170.
      ?mun wdt:P131+ ?dep.
      ?dep wdt:P31 wd:Q6465.
        SERVICE wikibase:label {
        bd:serviceParam wikibase:language "ca".
        }
    }"""
    endpoint_url = "https://query.wikidata.org/sparql"
    results = get_results(endpoint_url, query)
    for mon in results["results"]["bindings"]:
        qmun=mon["mun"]["value"].replace("http://www.wikidata.org/entity/","")
        nommun=mon["munLabel"]["value"].strip()
        nomdep=mon["depLabel"]["value"].strip()
        nomdesamb=(nommun+" ("+nomdep+")").casefold()
        if nomdesamb not in dicinvers.keys():
            dicinvers[nomdesamb]=qmun
    # desar
    if desa:
        fitxer = r"municipis.pkl"
        pickle.dump((dicdirecte, dicinvers), open(fitxer, "wb"))
    return(dicdirecte, dicinvers)

def carrega_municipis():
    try:
        a,b=pickle.load(open(r"municipis.pkl", "rb"))
    except FileNotFoundError:
        print ("Fitxer municipis no trobat. Important de Wikidata.")
        a,b=get_municipis()
    return(a,b)

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
        fitxer = r"ipac.pkl"
        pickle.dump(dicipac, open(fitxer, "wb"))
    return(dicipac)

def carrega_ipac(disc=False):
    if disc==True:
        print ("Llegint del disc els IPAC existents a Wikidata")
        ipac = pickle.load(open(r"ipac.pkl", "rb"))
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
        fitxer = r"igpcv.pkl"
        pickle.dump(dicigpcv, open(fitxer, "wb"))
    return(dicigpcv)

def carrega_igpcv(disc=False):
    if disc==True:
        print ("Llegint del disc els igpcv existents a Wikidata")
        igpcv = pickle.load(open(r"igpcv.pkl", "rb"))
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
        fitxer = r"sipca.pkl"
        pickle.dump(dicid, open(fitxer, "wb"))
    return(dicid)

def carrega_sipca(disc=False):
    if disc==True:
        print ("Llegint del disc els sipca existents a Wikidata")
        sipca = pickle.load(open(r"sipca.pkl", "rb"))
    else:
        print ("Important amb una query els sipca existents a Wikidata")
        sipca = get_sipca()
    return (sipca)

def get_bic(desa=True):
    # monuments existents amb codi bic
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
        fitxer = r"bic.pkl"
        pickle.dump(dicbic, open(fitxer, "wb"))
    return(dicbic)

def carrega_bic(disc=False):
    if disc==True:
        print ("Llegint del disc els BIC existents a Wikidata")
        bic = pickle.load(open(r"bic.pkl", "rb"))
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
        fitxer = r"merimee.pkl"
        pickle.dump(dicbic, open(fitxer, "wb"))
    return(dicbic)

def carrega_merimee(disc=False):
    if disc==True:
        print ("Llegint del disc els Mérimée existents a Wikidata")
        base = pickle.load(open(r"merimee.pkl", "rb"))
    else:
        print ("Important amb una query els Mérimée existents a Wikidata")
        base = get_merimee()
    return (base)

def carrega_monwd(qitems, qtipusmun="Q2074737", mostra=True):
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
    ?ipac ?bic ?igpcv ?sipca ?merimee ?ajbcn ?diba ?url
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
      OPTIONAL {?item wdt:P12860 ?diba}
      OPTIONAL {?item wdt:P973 ?url}
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

def tria_instancia(nom0):
    nom = nom0.casefold()
    if re.match("forns? de( coure)? calç", nom):
        return("Q59772", "forn de calç")
    if re.match("forns? de( coure)? guix", nom):
        return("Q81801249", "forn de guix")
    elif re.match("església|parròquia|basílica", nom):
        return("Q16970", "església")
    elif re.match("ermita", nom):
        return("Q56750657", "ermita")
    elif re.match("capell(et)?a ", nom):
        return("Q108325", "capella")
    elif re.match("hipogeu", nom):
        return("Q665247", "hipogeu")
    elif re.match("necròpolis", nom):
        return("Q200141", "necròpolis")
    elif re.match("d[oó]lmen", nom):
        return("Q101659", "dolmen")
    elif re.match("cement[ei]ri", nom):
        return("Q39614", "cementiri")
    elif re.match("tomb(a|es) ", nom):
        return("Q381885", "tomba")
    elif re.match("cov(a|es) ", nom):
        return("Q35509", "cova")
    elif re.match("(balm(a|es)|abric) ", nom):
        return("Q1149405", "balma")
    elif re.match("pedrer(a|es) ", nom):
        return("Q188040", "pedrera")
    elif re.match("ponts? |viaducte", nom):
        return("Q12280", "pont")
    elif re.match("aqüeducte", nom):
        return("Q474", "aqüeducte")
    elif re.match("creu de terme", nom):
        return("Q2309609", "creu de terme")
    elif re.match("creus? ", nom):
        return("Q17172602", "creu")
    elif re.match("monument[s] ", nom):
        return("Q4989906", "monument")
    elif re.match("(escultur|estàtu)(a|es)", nom):
        return("Q860861", "escultura")
    elif re.match("retaules? ceràmic", nom):
        return("Q97072190", "retaule ceràmic")
    elif re.match("calvari", nom):
        return("Q11331347", "calvari")
    elif re.match("(pous? de (gel|glaç|neu)|never(a|es) )", nom):
        return("Q3666499", "pou de gel")
    elif re.match("(font|brollador)s? ", nom):
        return("Q483453", "font")
    elif re.match("xemenei(a|es)", nom):
        return("Q2962545", "xemeneia") #xemeneia idustrial
    elif re.match("mas(ia)? ", nom):
        return("Q585956", "masia")
    elif re.match("finestr(a|es) ", nom):
        return("Q35473", "element arquitectònic")
    elif re.match("(llind(a|es)|dintells?) ", nom):
        return("Q1370517", "element arquitectònic")
    elif re.match("escuts? ", nom):
        return("Q245117", "element arquitectònic")
    elif re.match("búnquers? ", nom):
        return("Q91122", "búnquer")
    elif re.match("bord(a|es) ", nom):
        return("Q13231610", "borda")
    elif re.match("murall(a|es) ", nom):
        return("Q16748868", "muralla") #muralla urbana
    elif re.match("claustres? ", nom):
        return("Q1430154", "claustre") #muralla urbana
    else:
        return("Q41176", "edifici")

# el programa comença aquí
treubcil=False
posabcil=False
nocommons=False
iddisc=False
treucoor=False
verbose=False
verbose1=False
nocrea=False
creatot=False
mostra=False
toldist=.11
posarurldiba=False #posar P973 dels mapes de patrimonicultural
sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
arguments = sys.argv[1:]
if len(arguments)>0:
    if "-treubcil" in arguments:
        treubcil=True
        arguments.remove("-treubcil")
    if "-posabcil" in arguments:
        posabcil=True
        arguments.remove("-posabcil")
    if "-nocommons" in arguments:
        nocommons=True
        arguments.remove("-nocommons")
    if "-ipacdisc" in arguments:
        iddisc=True
        arguments.remove("-ipacdisc")
    if "-iddisc" in arguments:
        iddisc=True
        arguments.remove("-iddisc")
    if "-treucoor" in arguments:
        treucoor=True
        arguments.remove("-treucoor")
    if "-nocrea" in arguments:
        nocrea=True
        arguments.remove("-nocrea")
    if "-creatot" in arguments:
        creatot=True
        arguments.remove("-creatot")
    if "-verbose" in arguments:
        verbose=True
        toldist=.06
        arguments.remove("-verbose")
    if "-verbose1" in arguments:
        verbose=True
        verbose1=True
        toldist=.04
        arguments.remove("-verbose1")
if len(arguments)>0:
    nomllista=" ".join(arguments)
else:
    print("Manca el nom de la llista de monuments. Agafem opció per defecte")
    nomllista="Llista de monuments de l'Eixample de Barcelona"
site=pwb.Site('ca')
print (nomllista)
monllista, llistaq, faltenq, cataleg =monllistes(nomllista, site=site)
#print(llistaq)
print("Catàleg:",cataleg)
nh = len(llistaq)
nf = len(faltenq)
print(nh+nf, " monuments: ", nh, " amb Wikidata i ", nf, " per crear")
if len(faltenq)>0 and nocrea==False:
    #print ("Important codis existents a Wikidata")
    ipacexist=carrega_ipac(iddisc or cataleg!="ipac")
    igpcvexist=carrega_igpcv(iddisc or cataleg!="igpcv")
    bicexist=carrega_bic(iddisc or (cataleg!="igpcv" and cataleg!="bic"))
    sipcaexist=carrega_sipca(iddisc or cataleg!="bic")
    merimeeexist=carrega_merimee(iddisc or cataleg!="mh")
diccestat = {"and":"Q228", "mh":"Q142", "sard":"Q38"}
dicctipusmun = {"and":"Q24279", "mh":"Q484170", "sard":"Q747074"}
if cataleg in diccestat:
    qestat=diccestat[cataleg]
    qtipusmun=dicctipusmun[cataleg]
else:
    qestat="Q29"
    qtipusmun="Q2074737"
print("Important monuments de Wikidata")
monwd=carrega_monwd(llistaq, qtipusmun, mostra=verbose1)
#print(monwd) #
for id in faltenq:
    monwd[id]={}
print("Carregant diccionaris de municipis")
dicqmun,dicmunq = carrega_municipis()
# canviem municipis homònims segons la zona (plantilla filera)
if cataleg=="igpcv":
    dicmunq.update({"la mata":"Q1901661", "cabanes":"Q1646899", 
    "figueres":"Q1983382", "torrent":"Q161945", "corbera":"Q2045828", 
    "millars":"Q34254"})
elif cataleg=="ipac":
    dicmunq.update({"cabanes":"Q11257", "figueres":"Q6839",
    "torrent":"Q13572", "montblanc":"Q761735", "pau":"Q11799", "la garriga":"Q15415",
    "massanes":"Q13637", "l'escala":"Q11304", "anglès":"Q13027", "flaçà":"Q13430",
    "navès":"Q1917511", "avinyó":"Q16678","artés":"Q16677"})
elif cataleg=="mh":
    # ambigus amb altres llocs
    dicmunq.update({"corbera":"Q338840", "millars":"Q1369210", "montblanc":"Q639920",
    "la garriga":"Q227636", "massanes":"Q1072996", "tolosa":"Q7880", "l'escala":"Q391103"})
    # no desambiguats a la Viquipèdia
    dicmunq.update({"ginhac":"Q1072156"})
else:
    dicmunq.update({"l'alguer":"Q166282"})
dicmunq["menorca"]="Q52636"
#for result in monwd: print(result)
#print(monwd)
#print(monwd.keys())
if cataleg == "and":
    diccprot = {"BIC":"Q5004973", "BI":"Q21095081"}
else:
    diccprot={}
    diccprot["BCIN"]="Q1019352"
    diccprot["BIC"]="Q23712"
    diccprot["BIC etnològic"]="Q23712"
    diccprot["BIC etnològics"]="Q23712"
    diccprot["BCIL"]="Q11910250"
    diccprot["BRL"]="Q11910247"
    diccprot["BRL etnològic"]="Q11910247"
    diccprot["BRL etnològics"]="Q11910247"
    diccprot["BIE"]="Q41477381"
    diccprot["BC"]="Q26934132"
    diccprot["Inv."]="Q10387575"
    diccprot["Cat."]="Q10387684"
diccestil={}
diccestil["romànic"]="Q46261"
diccestil["gòtic"]="Q176483"
diccestil["gòtic tardà"]="Q10924220"
diccestil["arquitectura medieval"]="Q1349760"
diccestil["renaixentista"]="Q236122"
diccestil["renaixentista"]="Q236122"
diccestil["renaixement"]="Q236122"
diccestil["barroc"]="Q840829"
diccestil["neoclàssic"]="Q54111"
diccestil["neoclassicisme"]="Q54111"
diccestil["neogòtic"]="Q186363"
diccestil["neomudèjar"]="Q614624"
diccestil["historicisme neogòtic"]="Q186363"
diccestil["historicista"]="Q51879601"
diccestil["historicisme"]="Q51879601"
diccestil["neoromànic"]="Q744373"
diccestil["modernisme"]="Q1122677"
diccestil["modernista"]="Q1122677"
diccestil["arquitectura popular"]="Q930314"
diccestil["popular"]="Q930314"
diccestil["obra popular"]="Q930314"
diccestil["arquitectura religiosa d'època barroca"]="Q930314" #andorra
diccestil["noucentisme"]="Q1580216"
diccestil["noucentista"]="Q1580216"
diccestil["eclecticisme"]="Q2479493"
diccestil["eclèctic"]="Q2479493"
diccestil["racionalisme"]="Q2535546"
diccestil["racionalista"]="Q2535546"
diccestil["arquitectura del ferro"]="Q900557"
instruccions=""
informe=""
if cataleg=="igpcv":
    diccestil["modernisme"]="Q47015062" #modernisme valencià
    diccestil["modernista"]="Q47015062"
for item in llistaq+faltenq:
    #print(item)
    igpcv_web = "No comprovat"
    puja_igpcv = True
    if item[0:3]=="NWD":
        if nocrea==True:
            continue
        if "id" in monllista[item].keys() and cataleg=="ipac":
            ipaclau= monllista[item]["id"].replace("IPA-","").strip()
            if ipaclau in ipacexist.keys():
                #print (monllista[item]["nomcoor"], item, " IPAC duplicat de:")
                #print (ipacexist[ipaclau])
                informe += monllista[item]["nomcoor"] + " IPAC DUPLICAT de "
                informe += ipacexist[ipaclau]["qmon"]+ " " + ipacexist[ipaclau]["nommon"] + "\n"
                continue
        if "bic" in monllista[item].keys() and cataleg=="igpcv":
            igpcvclau= monllista[item]["bic"]
            if igpcvclau in igpcvexist.keys():
                informe += monllista[item]["nomcoor"] + " IGPCV DUPLICAT de "
                informe += igpcvexist[igpcvclau]["qmon"]+ " " + igpcvexist[igpcvclau]["nommon"] + "\n"
                continue
        if "bic" in monllista[item].keys() and cataleg in ["igpcv", "bic"]:
            bicclau= monllista[item]["bic"]
            if bicclau in bicexist.keys():
                informe += monllista[item]["nomcoor"] + " BIC DUPLICAT de "
                informe += bicexist[bicclau]["qmon"]+ " " + bicexist[bicclau]["nommon"] + "\n"
                continue
        if "bic" in monllista[item].keys() and cataleg=="bic": #Aragó
            bicclau= monllista[item]["bic"]
            if bicclau in sipcaexist.keys():
                informe += monllista[item]["nomcoor"] + " SIPCA DUPLICAT de "
                informe += sipcaexist[bicclau]["qmon"]+ " " + sipcaexist[bicclau]["nommon"] + "\n"
                continue
        if "id" in monllista[item].keys() and cataleg=="mh": #França
            idclau= monllista[item]["id"]
            if idclau in merimeeexist.keys():
                informe += monllista[item]["nomcoor"] + " Mérimée DUPLICAT de "
                informe += merimeeexist[idclau]["qmon"]+ " " + merimeeexist[idclau]["nommon"] + "\n"
                continue
        #comprovar els codis dels monuments valencians que no siguin BIC abans de pujar-los
        if cataleg=="igpcv":
            if not monllista[item]["prot"]=="BIC":
                print(monllista[item]["nomcoor"])
                igpcv_web = igpcv_url(monllista[item]["idurl"])
                print("Codi IGPCV. Llista:", monllista[item]["bic"], "Generalitat:", igpcv_web)
                if igpcv_web==monllista[item]["bic"]:
                    print("Codis iguals. Es crearà l'element.")
                else:
                    if creatot:
                        print ("Codis diferents. No es pujarà el codi.")
                        puja_igpcv = False
                    else:
                        print ("Codis diferents. No es crea l'element.")
                        continue
        #comprovar que els BIC tinguin codi BIC (pensat pels monuments menorquins)
        if creatot==False and cataleg=="bic" and bool(re.match("BIC", monllista[item]["prot"])):
            if not bool(re.match("RI-", monllista[item]["bic"])):
                print(monllista[item]["nomcoor"])
                print ("Codi de la llista:", monllista[item]["bic"], "no és BIC. No es crea l'element.")
                continue
        indexq="LAST"
        instruccions = instruccions+"CREATE||"
    else:
        indexq=item
    # etiquetes
    if not("itemLabel" in monwd[item].keys()) or bool(re.match("Q[0-9]", monwd[item]["itemLabel"]["value"])):
        if verbose1:
            if not("itemLabel" in monwd[item].keys()):
                print(monwd[item].keys())
            else:
                print(monwd[item]["itemLabel"]["value"])
        instruccio = indexq+"|Lca|"+'"'+ monllista[item]["nomcoor"].split("(")[0].strip()+'"'
        instruccions = instruccions + instruccio +"||"
        instruccio = indexq+"|Aca|"+'"'+ monllista[item]["nomcoor"]+'"'
        instruccions = instruccions + instruccio +"||"
        instp31,denomino = tria_instancia(monllista[item]["nomcoor"])
        munnet = monllista[item]["municipi"].strip("[]").split("|")[0].split("(")[0].strip()
        #print (munnet)
        instruccio = indexq+"|Dca|"+'"'+ denomino +" "+ al(munnet)+'"'
        instruccions = instruccions + instruccio +"||"
        if indexq=="LAST":
            instruccio = indexq+"|Len|"+'"'+ monllista[item]["nomcoor"].split("(")[0].strip()+'"'
            instruccions = instruccions + instruccio +"||"
            instruccio = indexq+"|Den|"+'"'+ "Cultural heritage monument in "+ munnet+'"'
            instruccions = instruccions + instruccio +"||"
    # coordenades
    if "lat" in monllista[item].keys() and len(monllista[item]["lat"])>4:
        if "lat" in monwd[item].keys():
            latll = float(monllista[item]["lat"])
            lonll = float(monllista[item]["lon"])
            latwd = float(monwd[item]["lat"]["value"])
            lonwd = float(monwd[item]["lon"]["value"])
            dist = distgeo(latll, lonll, latwd, lonwd)
            #print(item, " distància llista-WD ", dist, " km")
            if dist>toldist:
                    informe = informe + "COORDENADES " + monllista[item]["nomcoor"] + " " + item 
                    informe = informe + " a "+str(round(dist,3))+" km de Wikidata"
                    informe = informe + " ("+str(round(latwd-latll,5))+", "+str(round(lonwd-lonll,5))+")"
                    if dist>.14 and dist<.16 and latwd-latll>.001 and latwd-latll<.0012 and lonwd-lonll>.0011 and lonwd-lonll<.0013:
                        if re.match(".*([Ee]sglésia|[Cc]apella|Sant).*[(]", monllista[item]["nomcoor"]):
                            informe = informe + " (coordenades a treure)"
                            if treucoor==True:
                                #Treu
                                instruccio = "-"+indexq+"|"+"P625"+"|"+"@"+str(latwd)+"/"+str(lonwd)
                                instruccions = instruccions + instruccio +"||"
                                #Posa
                                instruccio = indexq+"|"+"P625"+"|"+"@"+monllista[item]["lat"]+"/"+monllista[item]["lon"]
                                instruccio = instruccio + "|S143|Q199693"
                                instruccions = instruccions + instruccio +"||"
                    informe = informe + "\n"
        else:
            #print("Pujar coordenades")
            #print(monllista[item])
            #print(monwd[item])
            instruccio = indexq+"|"+"P625"+"|"+"@"+monllista[item]["lat"]+"/"+monllista[item]["lon"]
            instruccio = instruccio + "|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
            #print(instruccio)
    # estatus patrimonial
    if "prot" in monwd[item].keys(): #comprovar protecció
        protllista=""
        if  "id" in monllista[item].keys() and "IPA-" in monllista[item]["id"]:
            protllista = "Q28034408"
        if "prot" in monllista[item].keys() and monllista[item]["prot"]!="":
            if monllista[item]["prot"] in diccprot.keys():
                 protllista = diccprot[monllista[item]["prot"]]
            elif protllista=="" and (not("bic" in monllista[item].keys()) or not(bool(re.match("RI-5", monllista[item]["bic"])))):
                print (monllista[item]["nomcoor"], " Protecció no prevista:", monllista[item]["prot"])
                informe = informe + monllista[item]["nomcoor"]+" Protecció no prevista:"
                informe = informe + " '"+monllista[item]["prot"] +"'\n"
        if protllista=="" and "bic" in monllista[item].keys(): # previst per llistes balears
            #print(monllista[item]["bic"])
            if re.match("RI-5", monllista[item]["bic"]):
                protllista=diccprot["BIC"]
        if protllista != "":
            qprotwd = monwd[item]["prot"]["value"].replace("http://www.wikidata.org/entity/","")
            if protllista != qprotwd:
                if treubcil and protllista=="Q28034408" and qprotwd=="Q11910250": #treure BCIL
                    informe = informe + "Traient BCIL de "
                    informe = informe + monllista[item]["nomcoor"] + " " + item + "\n"
                    instruccio = "-"+indexq+"|P1435|Q11910250"
                    instruccions = instruccions + instruccio +"||"
                    instruccio = indexq+"|P1435|"+protllista
                    instruccio = instruccio + "|S143|Q199693" 
                    instruccions = instruccions + instruccio +"||"
                elif posabcil and protllista=="Q11910250" and qprotwd=="Q28034408":
                    informe = informe + "Posant BCIL en comptes d'inventariat a "
                    informe = informe + monllista[item]["nomcoor"] + " " + item + "\n"
                    instruccio = "-"+indexq+"|P1435|Q28034408"
                    instruccions = instruccions + instruccio +"||"
                    instruccio = indexq+"|P1435|"+protllista
                    instruccio = instruccio + "|S143|Q199693" 
                    instruccions = instruccions + instruccio +"||"
                elif verbose==True:# or qprotwd != "Q23712" or protllista != "Q1019352": #avisar
                    print (monllista[item]["nomcoor"], item, " Protecció diferent a la llista i a Wikidata:")
                    print ("Llista:", monllista[item]["prot"], ", Wikidata:", qprotwd)
                    #print (monwd[item])
                    informe = informe + monllista[item]["nomcoor"] + " " + item 
                    informe = informe + " té PROTECCIÓ diferent a la llista i a Wikidata:\n"
                    informe = informe + "Llista: " + protllista +" ("+monllista[item]["prot"]+")"
                    informe = informe + ", Wikidata: " + qprotwd 
                    informe = informe + " (" + monwd[item]["protLabel"]["value"] + ")\n"
    else: #posar protecció
        if "prot" in monllista[item].keys() and monllista[item]["prot"] in diccprot.keys():
            protllista=diccprot[monllista[item]["prot"]]
            instruccio = indexq+"|P1435|"+protllista
            instruccio = instruccio + "|S143|Q199693" 
            instruccions = instruccions + instruccio +"||"
        elif "id" in monllista[item].keys() and "IPA-" in monllista[item]["id"]:
            instruccio = indexq+"|P1435|Q28034408|S248|Q1393661" 
            instruccions = instruccions + instruccio +"||"
        elif "bic" in monllista[item].keys(): # previst per llistes balears
            if re.match("RI-5", monllista[item]["bic"]):
                instruccio = indexq+"|P1435|Q23712|S143|Q199693" 
                instruccions = instruccions + instruccio +"||"
    # imatge
    if not ("imatge" in monwd[item].keys()):
        if "imatge" in monllista[item].keys() and len(monllista[item]["imatge"])>4:
            imatgeposar = monllista[item]["imatge"].replace("http://commons.wikimedia.org/wiki/Special:FilePath/","")
            imatges_prohibides = ["blanc.png"]
            if not (imatgeposar.casefold() in imatges_prohibides):
                instruccio = indexq+"|P18|"+'"'+imatgeposar+'"|S143|Q199693'
                instruccions = instruccions + instruccio +"||"
    # commonscat
    if "commonscat" in monllista[item].keys() and len(monllista[item]["commonscat"])>2:
        if "ccat" in monwd[item].keys():
            if monllista[item]["commonscat"] != monwd[item]["ccat"]["value"]:
                informe = informe + "COMMONSCAT DIFERENT a " + monllista[item]["nomcoor"] + " " + item + "\n"
                informe = informe + "Llista: " + monllista[item]["commonscat"]
                informe = informe + ", Wikidata: "+ monwd[item]["ccat"]["value"] + "\n"
        else:
            instruccio = indexq+"|P373|"+'"'+monllista[item]["commonscat"]+'"'#+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
    # sitelink de Commons
    if not(nocommons) and not ("commonslink" in monwd[item].keys()) and "commonscat" in monllista[item].keys() and len(monllista[item]["commonscat"])>2:
        instruccio = indexq+"|Scommonswiki|"+'"Category:'+monllista[item]["commonscat"]+'"'
        instruccions = instruccions + instruccio +"||"
    # codi IPAC
    if not ("ipac" in monwd[item].keys()) and "id" in monllista[item].keys() and "IPA-" in monllista[item]["id"]:
        posaipac=monllista[item]["id"].replace("IPA-","")
        if len(posaipac)>0:
            instruccio = indexq+"|P1600|"+'"'+posaipac+'"'#+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
    elif "ipac" in monwd[item].keys() and "id" in monllista[item].keys() and "IPA-" in monllista[item]["id"]:
        ipacwd = monwd[item]["ipac"]["value"]
        ipacllista = monllista[item]["id"].replace("IPA-","")
        if (ipacwd != ipacllista):
            informe = informe + "IPAC DIFERENT a " + monllista[item]["nomcoor"] + " " + item + "\n"
            informe = informe + "Llista: " + ipacllista
            informe = informe + ", Wikidata: "+ ipacwd + "\n"            
    # llegir de la llista codis BIC i IGPCV
    bicllista=""         
    igpcvllista=""
    sipcallista=""
    if "bic" in monllista[item].keys(): # llistes valencianes i aragoneses
        #print(monllista[item]["bic"])
        if re.match("RI-5", monllista[item]["bic"]):
            bicllista=monllista[item]["bic"]
        elif re.match("(12|46|03)", monllista[item]["bic"]): #valencianes
            igpcvllista=monllista[item]["bic"]
        elif re.match("[17]-INM", monllista[item]["bic"]): #aragoneses
            sipcallista=monllista[item]["bic"]
    if bicllista=="" and "id" in monllista[item].keys(): # llistes catalanes
        #print(monllista[item]["id"])
        if re.match("RI-5", monllista[item]["id"]):
            bicllista=monllista[item]["id"]
    # codi BIC
    if bicllista != "":
        #print ("BIC:",bicllista)
        if not ("bic" in monwd[item].keys()):
            #print (monwd[item].keys())
            instruccio = indexq+"|P808|"+'"'+bicllista+'"'+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
        elif bicllista != monwd[item]["bic"]["value"]:
            informe = informe + "BIC DIFERENT a " + monllista[item]["nomcoor"] + " " + item + "\n"
            informe = informe + "Llista: " + bicllista
            informe = informe + ", Wikidata: "+ monwd[item]["bic"]["value"] + "\n"            
    # codi IGPCV 
    if igpcvllista!="": 
        if not ("igpcv" in monwd[item].keys()) and protllista=="Q23712": # només els BIC (no em fio del codi dels altres)
            #print (monwd[item].keys())
            instruccio = indexq+"|P2473|"+'"'+igpcvllista+'"'#+"|S143|Q199693"
            if cataleg=="igpcv" and "idurl" in monllista[item].keys() and len(monllista[item]["idurl"])>1:
                instruccio = instruccio + "|S248|Q29787385"
                instruccio = instruccio + '|S854|"http://eduwp.edu.gva.es/patrimonio-cultural/ficha-inmueble.php?id='
                instruccio = instruccio +str(monllista[item]["idurl"])+'&lang=ca"'
            instruccions = instruccions + instruccio +"||"
        elif "igpcv" in monwd[item].keys() and igpcvllista != monwd[item]["igpcv"]["value"]:
            if igpcv_web == "No comprovat":
                igpcv_web = igpcv_url(monllista[item]["idurl"])
            informe = informe + "IGPCV DIFERENT a " + monllista[item]["nomcoor"] + " " + item + "\n"
            informe = informe + "Llista: " + igpcvllista
            informe = informe + ", Wikidata: "+ monwd[item]["igpcv"]["value"]
            informe = informe + ", Patrimoni: "+ igpcv_web + "\n"
        elif not("igpcv" in monwd[item].keys()) and cataleg=="igpcv" and "idurl" in monllista[item].keys(): #no BIC, comprovar codi)
            if igpcv_web == "No comprovat":
                igpcv_web = igpcv_url(monllista[item]["idurl"])
            if igpcv_web==monllista[item]["bic"]:
                instruccio = indexq+"|P2473|"+'"'+igpcvllista+'"'#+"|S143|Q199693"
                if cataleg=="igpcv" and "idurl" in monllista[item].keys() and len(monllista[item]["idurl"])>1:
                    instruccio = instruccio + "|S248|Q29787385"
                    instruccio = instruccio + '|S854|"http://eduwp.edu.gva.es/patrimonio-cultural/ficha-inmueble.php?id='
                    instruccio = instruccio +str(monllista[item]["idurl"])+'&lang=ca"'
                instruccions = instruccions + instruccio +"||"   
            else:
                informe = informe + "IGPCV diferents a la llista i a Patrimoni a " + monllista[item]["nomcoor"] + " " + item + "\n"
                informe = informe + "Llista: " + monllista[item]["bic"] + " "
                informe = informe + ", Web de Patrimoni: " + igpcv_web + "\n"
    # codi SIPCA
    if sipcallista != "":
        if not ("sipca" in monwd[item].keys()):
            #print (monwd[item].keys())
            instruccio = indexq+"|P3580|"+'"'+sipcallista+'"'#+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
        elif sipcallista != monwd[item]["sipca"]["value"]:
            informe = informe + "SIPCA DIFERENT a " + monllista[item]["nomcoor"] + " " + item + "\n"
            informe = informe + "Llista: " + sipcallista
            informe = informe + ", Wikidata: "+ monwd[item]["sipca"]["value"] + "\n"            
    # codi Mérimée
    if cataleg=="mh" and not ("merimee" in monwd[item].keys()) and "id" in monllista[item].keys():
        posamerimee=monllista[item]["id"]
        if len(posamerimee)>0:
            instruccio = indexq+"|P380|"+'"'+posamerimee+'"'#+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
    elif "merimee" in monwd[item].keys() and "id" in monllista[item].keys():
        merimeewd = monwd[item]["merimee"]["value"]
        merimeellista = monllista[item]["id"]
        if (merimeewd != merimeellista):
            informe = informe + "Mérimée DIFERENT a " + monllista[item]["nomcoor"] + " " + item + "\n"
            informe = informe + "Llista: " + merimeellista
            informe = informe + ", Wikidata: "+ merimeewd + "\n"            
    # municipi
    if "municipi" in monllista[item].keys() and len(monllista[item]["municipi"])>1: 
        nomunallista = re.split("[\]\|\(]", monllista[item]["municipi"].casefold())[0].strip(" [[]].,")
        try:
            munllista = dicmunq[nomunallista]
        except KeyError:
            print (nomunallista, "municipi desconegut")
            nomunallista = re.split("[\(\]\|]", nomunallista)[0].strip(" [[]].,")
            try:
                munllista = dicmunq[nomunallista]
            except KeyError:
                print (nomunallista, "municipi desconegut")
                munllista = "municipi desconegut"
        if "mun" in monwd[item].keys():
            munwd = monwd[item]["mun"]["value"].replace("http://www.wikidata.org/entity/","")
            if munllista != munwd:
                informe = informe + "MUNICIPIS diferents a " + monllista[item]["nomcoor"] + " " + item + "\n"
                informe = informe + "Llista: " + monllista[item]["municipi"] + " " + munllista
                informe = informe + ", Wikidata: " + munwd + "\n"
        else:
            instruccio = indexq+"|P131|"+munllista+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
    else:
        informe = informe + "Manca municipi a la llista a " + monllista[item]["nomcoor"] + " " + item + "\n"
    # codi ajuntament bcn
    if nomunallista == "barcelona" and "idurl2" in monllista[item].keys() and len(monllista[item]["idurl2"])>2:
        #print(monllista[item]["idurl2"])
        ajbcnllista = re.sub("^ *bcn/","",monllista[item]["idurl2"]).strip()
        #print(ajbcnllista)
        if re.match("^[0-9][0-9]/[0-9]+$", ajbcnllista):
            ajbcnllista = re.sub("^[01][0-9]/","", ajbcnllista)
        if re.match("^[0-9]+$", ajbcnllista):
            if "ajbcn" in monwd[item].keys():
                ajbcnwd = monwd[item]["ajbcn"]["value"]
                #print("Wikidata:", ajbcnwd)
                if ajbcnllista != ajbcnwd:
                    informe = informe + "Codis ajuntament Barcelona diferents a " + monllista[item]["nomcoor"] + " " + item + "\n"
                    informe = informe + "Llista: " + ajbcnllista
                    informe = informe + ", Wikidata: " + ajbcnwd + "\n"
            else:
                instruccio = indexq+"|P11557|"+'"'+ajbcnllista+'"'+"|S143|Q199693"
                instruccions = instruccions + instruccio +"||"
                instruccio = indexq+"|P1435|Q112668687|S143|Q199693"
                instruccions = instruccions + instruccio +"||"
        else:
                informe = informe + "Codi ajuntament incorrecte a " + monllista[item]["nomcoor"] + " " + item + "\n"
                informe = informe + "Codi:" + ajbcnllista + "\n"
                print("Codi ajuntament incorrecte a " + monllista[item]["nomcoor"] + " " + item)
    # codi diba com a "descrit a la url" i com a identificador
    if "idurl2" in monllista[item].keys() and len(monllista[item]["idurl2"])>2:
        #print(monllista[item]["idurl2"])
        if re.match("^diba/.*$", monllista[item]["idurl2"]):
            urldiba = re.sub("^diba/", "https://patrimonicultural.diba.cat/element/", monllista[item]["idurl2"])
            # en proves:
            #print(urldiba)
            if posarurldiba:
                if "url" in monwd[item].keys():
                    print("Wikidata:", monwd[item]["url"]["value"])
                else:
                    instruccio = indexq+"|P973|"+'"'+urldiba+'"'+"|P407|Q7026|S143|Q199693"
                    instruccions = instruccions + instruccio +"||"
            iddiba = re.sub("^diba/", "", monllista[item]["idurl2"])
            if "diba" in monwd[item].keys():
                print("Wikidata:", monwd[item]["diba"]["value"])
            else:
                print(monwd[item])
                instruccio = indexq+"|P12860|"+'"'+iddiba+'"'+"|S143|Q199693"
                instruccions = instruccions + instruccio +"||"
    # estil
    if "estil" in monllista[item].keys() and len(monllista[item]["estil"])>3:
        estil0 = monllista[item]["estil"].casefold().replace("[[","").replace("]]","")
        if estil0 in diccestil.keys():
            qestil = diccestil[estil0]
        else:
            estil0 = monllista[item]["estil"].split("<")[0].casefold().strip(" ")
            if estil0 in diccestil.keys():
                qestil = diccestil[estil0]
            else:
                qestil = ""
                if verbose1:
                    print(item, "estil desconegut", estil0)
        if qestil != "":
            if "estil" in monwd[item].keys():
                estilwd = monwd[item]["estil"]["value"].replace("http://www.wikidata.org/entity/","")
                if estilwd != qestil and verbose==True and (verbose1==True or estil0 != monwd[item]["estilLabel"]["value"].casefold()):
                    informe = informe + "Estils diferents a " + monllista[item]["nomcoor"] + " " + item + "\n"
                    informe = informe + "Llista: " + estil0 + " (" + qestil+"), "
                    informe = informe + "Wikidata: " + monwd[item]["estilLabel"]["value"] + " (" + estilwd + ")\n"
            else:
                instruccio = indexq+"|P149|"+qestil+"|S143|Q199693"
                instruccions = instruccions + instruccio +"||"
    #print(item, monwd[item].keys())
    #print(item, monllista[item].keys())
    #print(item, monllista[item].keys())
    if not("conserva" in monwd[item].keys()) and "lloc" in monllista[item].keys():
        #print(monllista[item]["lloc"]+monllista[item]["nom"])
        if re.search("(?<![Cc]ap )([Ee]nderroca|[Dd]es(apare(gu|ixe)|stru[ïi]))(t|da|r)", monllista[item]["lloc"]+monllista[item]["nom"]):
                instruccio = indexq+"|P5816|Q56556915|S143|Q199693"
                instruccions = instruccions + instruccio +"||"
    if not("estat" in monwd[item].keys()):
        instruccions = instruccions + indexq+"|P17|"+qestat+"||"
    if not("inst" in monwd[item].keys()):
        instp31,denomino = tria_instancia(monllista[item]["nomcoor"])
        instruccions = instruccions + indexq+"|P31|"+instp31+"||"
    else:
        #print(monwd[item]["inst"]["value"], monwd[item]["instLabel"]["value"])
        instwd = monwd[item]["inst"]["value"].replace("http://www.wikidata.org/entity/","")
        if instwd in ["Q4167410", "Q18091489"]:
            informe = informe + "DESAMBIGUACIÓ a " + monllista[item]["nomcoor"] + " " + item + "\n"
            informe = informe +  monwd[item]["instLabel"]["value"] + "\n"
print("Instruccions pel quickstatements:")
print(instruccions,"\n")
print(informe)
print("Duplicats:", " ".join([x for x,v in Counter(llistaq).items() if v>1]))
redireccions = [item for item in llistaq if len(monwd[item].keys())<=2]
print("Redireccions:", " ".join(redireccions))
redireccions = ["[[:d:"+x+"]]" for x in redireccions]
print("Redireccions:", ", ".join(redireccions))