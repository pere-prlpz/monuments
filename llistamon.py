# Funcions per llegir una llista de monuments i pujar a Wikidata les dades que faltin.
# Al final genera un informe de diferències i les instruccions pel quickstatements.
# Fa servir el paràmetre wikidata com a clau i crea items amb les fileres que no en tinguin.
# La llista se li dóna com a paràmetre extern. Per exemple:
# python llistamon.py "Llista de monuments de Viladrau"
# Les cometes són opcionals.
# Paràmetres generals:
# -nocommons: no posa el sitelink de commons (útil quan algun ja està enllaçat a Wikidata i quickstatemens dóna error)
# -ipacdisc: no importa tots els item amb codi IPAC de Wikidata (P1600) sinó que fa servir la versió guardada el darrer cop.
# -verbose: més sensible a informar de diferències (menys diferència coordenades, estils amb id diferent que es diuen igual, etc.)
# Paràmetres per esborrar dades:
# El programa no esborra ni canvia propietats que ja estiguin a Wikidata excepte amb els següents paràmetres
# (utilitzeu-los amb prudència):
# -treubcil: treu P1435=BCIL de Wikidata quan a la llista són béns inventariats
# -posabcil: treu P1435=Inventariat de Wikidata quan a la llista són BCIL
# -treucoor: canvia les coordenades existents a Wikidata per les de la llista. Només per suposats errors de datum amb esglésies. (en implementació)
#
# PER FER:
# Comprovar si IPAC diferent
# Comprovar si hi ha descripció i fer-ne
# Fer etiquetes i descripcions en anglès i més llengües
# Reconèixer i pujar dos estils junts
# Buscar diferències llistes/wikidata (en els paràmetres que falten)
# Treballar per categories de llistes en comptes de llistes individuals
# Adaptar-lo a plantilles de monumenst diferents de fileraIPA i monuments no catalans
# Adaptar-lo a patrimoni natural, arbres singulars i rellotges de sol
# Reconèixer quan sitecommons ja està agafat

import pywikibot as pwb
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
    sn1=sn[:]
    #print(sn,sn1)
    sn1 = re.sub("^[Ee]l ","al ",sn1)
    #print(sn,sn1)
    sn1 = re.sub("^[Ee]ls ","als ",sn1)
    sn1 = re.sub("^L'","a l'",sn1)
    sn1 = re.sub("^La ","a la ",sn1)
    sn1 = re.sub("^Les ","a les ",sn1)
    #print(sn,sn1)
    if sn1==sn:
        sn1="a "+sn
    #print(sn,sn1)
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

def monunallista(llista, filera=pwb.Page(pwb.Site('ca'), "Plantilla:Filera IPA")):
# Retorna diccionari amb els monuments d'una llista de monuments
# i una llista amb els paràmetres wikidata.
# Fa servir el paràmetre wikidata com a clau.
# Els que no en tenen els dóna un índex provisional.
# Al diccionari sobreescriu els duplicats.
    plantilles = pag.templatesWithParams()
    monllista = {}
    monq = []
    monnoq = []
    ni = 1
    for plantilla in plantilles:
      #print(plantilla[0])
      if plantilla[0]==filera:
        params=treuparams(plantilla)
        if "wikidata" in params.keys() and len(params["wikidata"])>2:
            index=params["wikidata"]
            monq.append(index)
        else:
            index="NWD"+str(ni)
            ni=ni+1
            monnoq.append(index)
        monllista[index]=params
    return(monllista, monq, monnoq)


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
    query = """SELECT DISTINCT ?mun ?munLabel ?munAltLabel ?oficial
    WHERE {
        ?mun wdt:P31 wd:Q33146843.
        OPTIONAL {?mun wdt:P1448 ?oficial}
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
        dicinvers[nommun.casefold()]=qmun
        if "oficial" in mon.keys():
            nomoficial=mon["oficial"]["value"]
            if not(nomoficial in dicinvers.keys()): 
                dicinvers[nomoficial.casefold()]=qmun
        if "munAltLabel" in mon.keys():
            alies=mon["munAltLabel"]["value"]
            if len(alies)>1 and not(alies.casefold() in dicinvers.keys()):
                dicinvers[alies.casefold()]=qmun           
    if desa:
        fitxer = r"C:\Users\Pere\Documents\perebot\municipis.pkl"
        pickle.dump((dicdirecte, dicinvers), open(fitxer, "wb"))
    return(dicdirecte, dicinvers)

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

def carrega_monwd(qitems):
    n = len(qitems)
    print(n,"elements per carregar")
    if n<150:
        inicis=[0]
        finals=[n]
    else:
        mig=round(n/2)
        inicis=[0, mig]
        finals=[mig, n]
    monuments={}
    for i in range(len(inicis)):
        print("carregant lot",i)
        monuments.update(get_monwd(qitems[inicis[i]:finals[i]]))
    print(len(monuments), "monuments llegits en", len(inicis),"fases")
    return(monuments)

def get_monwd(qitems):
    #print(qitems)
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

def carrega_municipis():
    try:
        a,b=pickle.load(open(r"C:\Users\Pere\Documents\perebot\municipis.pkl", "rb"))
    except FileNotFoundError:
        print ("Fitxer municipis no trobat. Important de Wikidata.")
        a,b=get_municipis()
    return(a,b)

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
    elif re.match("pous? de (gel|glaç|neu)", nom):
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
    elif re.match("búnquer? ", nom):
        return("Q91122", "búnquer")
    elif re.match("bord(a|es) ", nom):
        return("Q13231610", "borda")
    else:
        return("Q41176", "edifici")

# el programa comença aquí
treubcil=False
posabcil=False
nocommons=False
ipacdisc=False
treucoor=False
verbose=False
toldist=.11
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
        ipacdisc=True
        arguments.remove("-ipacdisc")
    if "-treucoor" in arguments:
        treucoor=True
        arguments.remove("-treucoor")
    if "-verbose" in arguments:
        verbose=True
        toldist=.06
        arguments.remove("-verbose")

if len(arguments)>0:
    nomllista=" ".join(arguments)
else:
    print("Manca el nom de la llista de monuments. Agafem opció per defecte")
    nomllista="Llista de monuments de l'Eixample de Barcelona"
site=pwb.Site('ca')
pag = pwb.Page(site, nomllista)
#pag = pwb.Page(site, "Usuari:PereBot/taller")
print (pag)
#print(monunallista(pag))
monllista, llistaq, faltenq =monunallista(pag)
#print(llistaq)
#print(faltenq)
nh = len(llistaq)
nf = len(faltenq)
print(nh+nf, " monuments: ", nh, " amb Wikidata i ", nf, " per crear")
if len(faltenq)>0:
    #print ("Important IPAC existents de Wikidata")
    ipacexist=carrega_ipac(ipacdisc)
print("Important monuments de Wikidata")
monwd=carrega_monwd(llistaq)
for id in faltenq:
    monwd[id]={}
print("Carregant diccionaris de municipis")
dicqmun,dicmunq = carrega_municipis()
#for result in monwd: print(result)
#print(monwd)
#print(monwd.keys())
diccprot={}
diccprot["BCIN"]="Q1019352"
diccprot["BIC"]="Q23712"
diccprot["BCIL"]="Q11910250"
diccestil={}
diccestil["romànic"]="Q46261"
diccestil["gòtic"]="Q176483"
diccestil["gòtic tardà"]="Q10924220"
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
diccestil["noucentisme"]="Q1580216"
diccestil["noucentista"]="Q1580216"
diccestil["eclecticisme"]="Q2479493"
diccestil["eclèctic"]="Q2479493"
diccestil["racionalisme"]="Q2535546"
diccestil["racionalista"]="Q2535546"
diccestil["arquitectura del ferro"]="Q900557"
instruccions=""
informe=""
for item in llistaq+faltenq:
    #print(item)
    if item[0:3]=="NWD":
        ipaclau= monllista[item]["id"].replace("IPA-","")
        if ipaclau in ipacexist.keys():
            #print (monllista[item]["nomcoor"], item, " IPAC duplicat de:")
            #print (ipacexist[ipaclau])
            informe += monllista[item]["nomcoor"] + " IPAC DUPLICAT de "
            informe += ipacexist[ipaclau]["qmon"]+ " " + ipacexist[ipaclau]["nommon"] + "\n"
            continue
        indexq="LAST"
        instruccions = instruccions+"CREATE||"
        instruccio = "LAST|Lca|"+'"'+ monllista[item]["nomcoor"].split("(")[0].strip()+'"'
        instruccions = instruccions + instruccio +"||"
        instruccio = "LAST|Aca|"+'"'+ monllista[item]["nomcoor"]+'"'
        instruccions = instruccions + instruccio +"||"
        instp31,denomino = tria_instancia(monllista[item]["nomcoor"])
        instruccio = "LAST|Dca|"+'"'+ denomino +" "+ al(monllista[item]["municipi"])+'"'
        instruccions = instruccions + instruccio +"||"
        #instruccions = instruccions + "LAST|P31|Q41176||"
    else:
        indexq=item
    if "lat" in monllista[item].keys() and len(monllista[item]["lat"])>4:
        if "lat" in monwd[item].keys():
            latll = float(monllista[item]["lat"])
            lonll = float(monllista[item]["lon"])
            latwd = float(monwd[item]["lat"]["value"])
            lonwd = float(monwd[item]["lon"]["value"])
            dist = distgeo(latll, lonll, latwd, lonwd)
            #print(item, " distància llista-WD ", dist, " km")
            if dist>toldist:
                    informe = informe + monllista[item]["nomcoor"] + " " + item 
                    informe = informe + " COORDENADES a "+str(round(dist,3))+" km de Wikidata"
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
    if "prot" in monwd[item].keys(): #comprovar protecció
        protllista=""
        if  "id" in monllista[item].keys() and "IPA-" in monllista[item]["id"]:
            protllista = "Q28034408"
        if "prot" in monllista[item].keys() and monllista[item]["prot"]!="":
            if monllista[item]["prot"] in diccprot.keys():
                 protllista = diccprot[monllista[item]["prot"]]
            elif protllista=="":
                print (monllista[item]["nomcoor"], " Protecció no prevista:", monllista[item]["prot"])
                informe = informe + monllista[item]["nomcoor"]+" Protecció no prevista:"
                informe = informe + " '"+monllista[item]["prot"] +"'\n"
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
                else: #avisar
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
            protposar=diccprot[monllista[item]["prot"]]
            instruccio = indexq+"|P1435|"+protposar
            instruccio = instruccio + "|S143|Q199693" 
            instruccions = instruccions + instruccio +"||"
        elif "id" in monllista[item].keys() and "IPA-" in monllista[item]["id"]:
            instruccio = indexq+"|P1435|Q28034408|S248|Q1393661" 
            instruccions = instruccions + instruccio +"||"
    if not ("imatge" in monwd[item].keys()):
        if "imatge" in monllista[item].keys() and len(monllista[item]["imatge"])>4:
            imatgeposar = monllista[item]["imatge"].replace("http://commons.wikimedia.org/wiki/Special:FilePath/","")
            instruccio = indexq+"|P18|"+'"'+imatgeposar+'"|S143|Q199693'
            instruccions = instruccions + instruccio +"||"
    if "commonscat" in monllista[item].keys() and len(monllista[item]["commonscat"])>2:
        if "ccat" in monwd[item].keys():
            if monllista[item]["commonscat"] != monwd[item]["ccat"]["value"]:
                informe = informe + "COMMONSCAT DIFERENT a " + monllista[item]["nomcoor"] + " " + item + "\n"
                informe = informe + "Llista: " + monllista[item]["commonscat"]
                informe = informe + ", Wikidata: "+ monwd[item]["ccat"]["value"] + "\n"
        else:
            instruccio = indexq+"|P373|"+'"'+monllista[item]["commonscat"]+'"'#+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
    if not(nocommons) and not ("commonslink" in monwd[item].keys()) and "commonscat" in monllista[item].keys() and len(monllista[item]["commonscat"])>2:
        instruccio = indexq+"|Scommonswiki|"+'"Category:'+monllista[item]["commonscat"]+'"'
        instruccions = instruccions + instruccio +"||"
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
    if "municipi" in monllista[item].keys() and len(monllista[item]["municipi"])>1: 
        nomunallista = monllista[item]["municipi"].casefold()
        munllista = dicmunq[nomunallista]
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
                print(item, "estil desconegut", estil0)
        if qestil != "":
            if "estil" in monwd[item].keys():
                estilwd = monwd[item]["estil"]["value"].replace("http://www.wikidata.org/entity/","")
                if estilwd != qestil and (verbose==True or estil0 != monwd[item]["estilLabel"]["value"]):
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
        if re.search("([Ee]nderroca|[Dd]es(apare(gu|ixe)|stru[ïi]))(t|da|r)", monllista[item]["lloc"]+monllista[item]["nom"]):
                instruccio = indexq+"|P5816|Q56556915|S143|Q199693"
                instruccions = instruccions + instruccio +"||"
    if not("estat" in monwd[item].keys()):
        instruccions = instruccions + indexq+"|P17|Q29||"
    if not("inst" in monwd[item].keys()):
        instp31,denomino = tria_instancia(monllista[item]["nomcoor"])
        instruccions = instruccions + indexq+"|P31|"+instp31+"||"

print("Instruccions pel quickstatements:")
print(instruccions,"\n")
print(informe)
print("Duplicats:", " ".join([x for x,v in Counter(llistaq).items() if v>1]))
print("Redireccions:", " ".join([item for item in llistaq if len(monwd[item].keys())<=2]))