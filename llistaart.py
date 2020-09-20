#-*- coding: utf-8 -*-
#
# Funcions per llegir llistes d'art públic i pujar a Wikidata les dades que faltin.


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
    sn1 = re.sub("^([AEIOUaeiouÀÈÉÍÒÓÚàèéíòóúHh])", r"d'\1", sn1)
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
            elif plantilla[0]==fileraArt:
                cat0="art"
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

def get_results(endpoint_url, query):
    user_agent = "PereBot/1.0 (ca:User:Pere_prlpz; prlpzb@gmail.com) Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()


def get_art(desa=True):
    # monuments existents amb codi art públic
    query = """SELECT DISTINCT ?mon ?monLabel ?art
    WHERE {
      ?mon wdt:P8601 ?art.
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
        dicipac[mon["art"]["value"]]={"qmon":qmon, "nommon":nommon}
    if desa:
        fitxer = r"C:\Users\Pere\Documents\perebot\art.pkl"
        pickle.dump(dicipac, open(fitxer, "wb"))
    return(dicipac)

def carrega_art(disc=False):
    if disc==True:
        print ("Llegint del disc els codis art públic existents a Wikidata")
        ipac = pickle.load(open(r"C:\Users\Pere\Documents\perebot\art.pkl", "rb"))
    else:
        print ("Important amb una query els codis art públic existents existents a Wikidata")
        ipac = get_art()
    return (ipac)

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
    ?ipac ?bic ?igpcv ?sipca ?merimee ?art
    ?mun ?estil ?estilLabel ?ccat ?commonslink ?estat ?conserva ?inst ?instLabel
    ?creador ?creadorLabel ?material ?materialLabel
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
      OPTIONAL {?item wdt:P8601 ?art}
      OPTIONAL {?item wdt:P373 ?ccat}
      OPTIONAL {?item wdt:P1600 ?ipac}
      OPTIONAL {?item wdt:P808 ?bic}
      OPTIONAL {?item wdt:P2473 ?igpcv}
      OPTIONAL {?item wdt:P3580 ?sipca}
      OPTIONAL {?item wdt:P380 ?merimee}
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
      OPTIONAL {?item wdt:P170 ?creador}
      OPTIONAL {?item wdt:P186 ?material}
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
    if re.match("mural", nom):
        return("Q219423", "mural")
    elif re.match("forns? de( coure)? calç", nom):
        return("Q59772", "forn de calç")
    elif re.match("forns? de( coure)? guix", nom):
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
    elif re.match("búnquer? ", nom):
        return("Q91122", "búnquer")
    elif re.match("bord(a|es) ", nom):
        return("Q13231610", "borda")
    elif re.match("murall(a|es) ", nom):
        return("Q16748868", "muralla") #muralla urbana
    elif re.match("edifici ", nom):
        return("Q41176", "edifici")
    else:
        return("Q860861", "obra escultòrica")


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
    nomllista="Llista de l'art públic de Nou Barris"
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
    artexist=carrega_art(iddisc or cataleg!="art")
qestat="Q29"
print("Important monuments de Wikidata")
monwd=carrega_monwd(llistaq, mostra=verbose1) #omès qtipusmun
for id in faltenq:
    monwd[id]={}
dicmunq={"barcelona":"Q1492"}
dicqmun={"Q1492":"barcelona"}
dicautor={"Francisco López Hernández":"Q3913010",
"Josep Clarà":"Q3042936",
"Josep Llimona":"Q3138880",
"Antoni Llena":"Q11905872",
"Jaume Otero":"Q14427271",
"Frederic Marès":"Q3397291",
"Eulàlia Fàbregas de Sentmenat":"Q15279578",
"Eusebi Arnau":"Q1584929",
"Venanci Vallmitjana":"Q4103087",
"Josep Maria Subirachs":"Q182136",
"Joan Miró":"Q152384",
"Josep Dunyach":"Q9013106",
"Pau Gargallo":"Q456991",
"Pablo Gargallo":"Q456991",
"Joan Borrell i Nicolau":"Q9011855",
"Xavier Corberó":"Q9096553",
"Rafael Atché":"Q11701796",
"Manuel Fuxà":"Q4493323",
"Rossend Nobas":"Q11703336",
"Eduard B. Alentorn":"Q1287884",
"Eduard Alentorn":"Q1287884",
"Pere Carbonell":"Q9058318",
"Antoni Tàpies":"Q158099",
"Andreu Alfaro":"Q328704",
"Perejaume":"Q550154",
"Jaume Plensa":"Q1396516",
"Josep Viladomat":"Q581424",
"Sol LeWitt":"Q168587",
"Joan Mora":"Q4025913",
"Josep Cañas":"Q11685502",
"Pedro Delso":"Q96379203",
"Agapit Vallmitjana i Barbany":"Q11481944",
"Enric Maurí":"Q93434878",
"Q15284689":"Q15284689",
"Lautaro Díaz":"Q15980653",
"Francesc Torres":"Q11922857"}#"":"",
dicmat={"pedra de Montjuïc":"Q17301659",
"pedra":"Q22731",
"granit":"Q3115353",
"pedra calcària":"Q23757",
"alabastre":"Q143447",
"marbre":"Q40861",
"marbre blanc":"Q40861",
"marbre verd":"Q40861",
"pedra artificial":"Q5049565",
"terracota":"Q60424",
"ceràmica":"Q45621",
"formigó":"Q22657",
"bronze":"Q34095",
"ferro colat":"Q483269",
"acer":"Q11427",
"acer inoxidable":"Q172587",
"fusta":"Q287"}
qestat = "Q29"
instruccions=""
informe=""
for item in llistaq+faltenq: #(llistaq+faltenq)[:5]: #per proves
    #print(item) #
    #print (monwd[item]) #
    if item[0:3]=="NWD":
        if nocrea==True:
            continue
        if "codi" in monllista[item].keys() and cataleg=="art":
            artclau= monllista[item]["codi"].strip()
            if re.match("08019/",artclau):  
                artclau = artclau.replace("08019/","")
                if artclau in artexist.keys():
                    #print (monllista[item]["títol"], item, " IPAC duplicat de:")
                    #print (artexist[artclau])
                    informe += monllista[item]["títol"] + " Codi art públic DUPLICAT de "
                    informe += artexist[artclau]["qmon"]+ " " + artexist[artclau]["nommon"] + "\n"
                    continue
        indexq="LAST"
        instruccions = instruccions+"CREATE||"
    else:
        indexq=item
    # escultor (de moment per descripció)
    nomautor = ""
    if "títol" in monllista[item].keys() and cataleg=="art":
        nomautor = re.sub(".*\((.*)\).*",r"\1", monllista[item]["títol"]).strip()
        if "autor" in monllista[item].keys() and nomautor in monllista[item]["autor"]:
            print ("Trobat autor", nomautor)
        else:
            print ("No trobat autor", nomautor) 
            nomautor = ""
    # etiquetes
    if not("itemLabel" in monwd[item].keys()) or bool(re.match("Q[0-9]", monwd[item]["itemLabel"]["value"])):
        if verbose1:
            if not("itemLabel" in monwd[item].keys()):
                print(monwd[item].keys())
            else:
                print(monwd[item]["itemLabel"]["value"])
        instruccio = indexq+"|Lca|"+'"'+ monllista[item]["títol"].split("(")[0].strip()+'"'
        instruccions = instruccions + instruccio +"||"
        instruccio = indexq+"|Aca|"+'"'+ monllista[item]["títol"]+'"'
        instruccions = instruccions + instruccio +"||"
        # com que no comprova si ja hi ha label en anglès, només l'afegeix als nous
        if item[0:3]=="NWD":
            instruccio = indexq+"|Len|"+'"'+ monllista[item]["títol"].split("(")[0].strip()+'"'
            instruccions = instruccions + instruccio +"||"
    # instància i descripció
    if not("inst" in monwd[item].keys()):
        instp31,denomino = tria_instancia(monllista[item]["títol"])
        instruccions = instruccions + indexq+"|P31|"+instp31+"||"
        munnet = monllista[item]["municipi"].strip("[]").split("|")[0].strip()
        #print (munnet)
        if nomautor == "":
            instruccio = indexq+"|Dca|"+'"'+ denomino +" "+ al(munnet)+'"'
        else:
            instruccio = indexq+"|Dca|"+'"'+ denomino +" "+de(nomautor) +" "+ al(munnet)+'"'
        instruccions = instruccions + instruccio +"||"
    # autor
    if nomautor in dicautor.keys() and not "creador" in monwd[item].keys():
        qautor = dicautor[nomautor]
        instruccio = indexq+"|"+"P170"+"|"+qautor + "|S143|Q199693"
        instruccions = instruccions + instruccio +"||"
    # material
    if not("material" in monwd[item].keys()):
        if "material" in monllista[item].keys():
            matllista = monllista[item]["material"].strip(" []")
            if matllista in dicmat.keys():
                posamat = dicmat[matllista]
                instruccio = indexq+"|"+"P186"+"|"+ posamat + "|S143|Q199693"
                instruccions = instruccions + instruccio +"||"
            else:
                print ("Material desconegut", monllista[item]["material"])
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
                    informe = informe + "COORDENADES " + monllista[item]["títol"] + " " + item 
                    informe = informe + " a "+str(round(dist,3))+" km de Wikidata"
                    informe = informe + " ("+str(round(latwd-latll,5))+", "+str(round(lonwd-lonll,5))+")"
                    if dist>.14 and dist<.16 and latwd-latll>.001 and latwd-latll<.0012 and lonwd-lonll>.0011 and lonwd-lonll<.0013:
                        if re.match(".*([Ee]sglésia|[Cc]apella|Sant).*[(]", monllista[item]["títol"]):
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
                informe = informe + "COMMONSCAT DIFERENT a " + monllista[item]["títol"] + " " + item + "\n"
                informe = informe + "Llista: " + monllista[item]["commonscat"]
                informe = informe + ", Wikidata: "+ monwd[item]["ccat"]["value"] + "\n"
        else:
            instruccio = indexq+"|P373|"+'"'+monllista[item]["commonscat"]+'"'#+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
    # sitelink de Commons
    if not(nocommons) and not ("commonslink" in monwd[item].keys()) and "commonscat" in monllista[item].keys() and len(monllista[item]["commonscat"])>2:
        instruccio = indexq+"|Scommonswiki|"+'"Category:'+monllista[item]["commonscat"]+'"'
        instruccions = instruccions + instruccio +"||"
    # estatus patrimonial
    if not ("prot" in monwd[item].keys()) or monwd[item]["prot"]["value"] != "http://www.wikidata.org/entity/Q15945449":
        if "codi" in monllista[item].keys() and "08019/" in monllista[item]["codi"]:
            arrel = "http://w10.bcn.es/APPS/gmocataleg_monum/FitxaMonumentAc.do?idioma=CA&codiMonumIntern="
            urlart = monllista[item]["idurl"].replace("bcn/",arrel)
            instruccio = indexq+"|P1435|Q15945449|S248|Q99433743|S854|"+'"'+urlart+'"'
            instruccions = instruccions + instruccio +"||"
            #instruccio = indexq+"|P1435|Q15945449|S143|Q199693"
            #instruccions = instruccions + instruccio +"||"
    # codi art públic
    if not ("art" in monwd[item].keys()) and "codi" in monllista[item].keys() and "08019/" in monllista[item]["codi"]:
        posaart=monllista[item]["codi"].replace("08019/","")
        if len(posaart)>0:
            arrel = "http://w10.bcn.es/APPS/gmocataleg_monum/FitxaMonumentAc.do?idioma=CA&codiMonumIntern="
            urlart = monllista[item]["idurl"].replace("bcn/",arrel)
            instruccio = indexq+"|P8601|"+'"'+posaart+'"'+"|P2699|"+'"'+urlart+'"'+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
    elif "art" in monwd[item].keys() and "codi" in monllista[item].keys() and "08019/" in monllista[item]["codi"]:
        artwd = monwd[item]["art"]["value"]
        artllista = monllista[item]["codi"].replace("08019/","")
        if (artwd != artllista):
            informe = informe + "codi art públic DIFERENT a " + monllista[item]["títol"] + " " + item + "\n"
            informe = informe + "Llista: " + artllista
            informe = informe + ", Wikidata: "+ artwd + "\n"            
    # estat sobirà
    if not("estat" in monwd[item].keys()):
        instruccions = instruccions + indexq+"|P17|"+qestat+"||"
    # municipi
    if "municipi" in monllista[item].keys() and len(monllista[item]["municipi"])>1: 
        nomunallista = re.split("[\]\|]", monllista[item]["municipi"].casefold())[0].strip(" [[]].,")
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
                informe = informe + "MUNICIPIS diferents a " + monllista[item]["títol"] + " " + item + "\n"
                informe = informe + "Llista: " + monllista[item]["municipi"] + " " + munllista
                informe = informe + ", Wikidata: " + munwd + "\n"
        else:
            instruccio = indexq+"|P131|"+munllista+"|S143|Q199693"
            instruccions = instruccions + instruccio +"||"
    else:
        informe = informe + "Manca municipi a la llista a " + monllista[item]["títol"] + " " + item + "\n"

print("Instruccions pel quickstatements:")
print(instruccions,"\n")
print(informe)
