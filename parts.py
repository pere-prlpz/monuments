# Funcions per llegir una llista de monuments
# i posar part de i format per a elements d'un conjunt
# Paràmetres:
# - Nom de la llista (entre cometes)
# - Item del conjunt (no calen cometes)
# - Patró per identificar els elements del conjunt pel valor de nomcoor. És un regexp que
# es fa servir amb re.match i per tand ha d'incloure el principi del nom. Les lletres
# han de ser en minúscula perquè es compara amb el paràmetre nomcoor amb minúscules.
# Exemple: 
# python parts.py "llista de monuments dels Serrans" Q5730144 "(escut|emblema).*de los olmos"
#
# PER FER:
# - Adaptar a més plantilles de filera (ara funciona amb IPAC i BIC Val i probablement amb BIC).

import pywikibot as pwb
from SPARQLWrapper import SPARQLWrapper, JSON
from collections import Counter
import math
import re
import pickle
import sys


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
    fileres=[fileraIPA, fileraBIC, fileraBICval]
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
    return(monllista, monq, monnoq, cat0)

# el programa comença aquí
arguments = sys.argv[1:]
if len(arguments)>0:
    nomllista=arguments[0]
    conjunt=arguments[1]
    patro=arguments[2]
    print(nomllista, conjunt, patro)
else:
    print("Manquen dades. Agafem opció per defecte")

    #dades (no utilitzades)
    nomllista="llista de monuments de Cervelló"
    conjunt="Q21790926"
    patro="forn de calç"

    #dades
    nomllista="llista de monuments del Barcelonès Nord"
    conjunt="Q11946861"
    patro="hospital de l'esperit sant"

    #dades
    nomllista="llista de monuments del Vallès Occidental"
    conjunt="Q56402584"
    patro="barraca de pedra seca"

site=pwb.Site('ca')
pag = pwb.Page(site, nomllista)
print (pag)
monllista, llistaq, faltenq, cataleg =monunallista(pag)
#print(llistaq)
#print(faltenq)
instruccions=""
informe=""
for item in llistaq:
    print(monllista[item]["nomcoor"].casefold())
    if bool(re.match(patro, monllista[item]["nomcoor"].casefold())) & (conjunt != item):
        instruccio1=conjunt+"|"+"P527"+"|"+item
        instruccio2=item+"|"+"P361"+"|"+conjunt
        instruccions=instruccions+instruccio1+"||"+instruccio2+"||"
   
print("Instruccions pel quickstatements:")
print(instruccions,"\n")
print(informe)
