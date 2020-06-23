# Funcions per llegir una llista de monuments
# i posar part de i format per a elements d'un conjunt
# Paràmetres:
# - Nom de la llista (entre cometes)
# - Item del conjunt (no calen cometes)
# - Patró per identificar els elements del conjunt pel valor de nomcoor. Com que es
#   fa servir amb match inclou el principi del nom.
#
# PER FER:

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

# Retorna diccionari amb els monuments d'una llista de monuments
# i una llista amb els paràmetres wikidata.
# Fa servir el paràmetre wikidata com a clau.
# Els que no en tenen no els inclou.
# Al diccionari sobreescriu els duplicats.
def monunallista(llista, filera=pwb.Page(pwb.Site('ca'), "Plantilla:Filera IPA")):
    plantilles = pag.templatesWithParams()
    monllista = {}
    monq = []
    monnoq = []
    ni = "NOWIKIDATA"
    for plantilla in plantilles:
      #print(plantilla[0])
      if plantilla[0]==filera:
        params=treuparams(plantilla)
        if "wikidata" in params.keys() and len(params["wikidata"])>2:
            index=params["wikidata"]
            monq.append(index)
        else:
            index=ni
            ni=ni+"1"
            monnoq.append(index)
        monllista[index]=params
    return(monllista, monq, monnoq)

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
monllista, llistaq, faltenq =monunallista(pag)
#print(llistaq)
#print(faltenq)
instruccions=""
informe=""
for item in llistaq:
    #print(monllista[item]["nomcoor"].casefold())
    if bool(re.match(patro, monllista[item]["nomcoor"].casefold())) & (conjunt != item):
        instruccio1=conjunt+"|"+"P527"+"|"+item
        instruccio2=item+"|"+"P361"+"|"+conjunt
        instruccions=instruccions+instruccio1+"||"+instruccio2+"||"
   
print("Instruccions pel quickstatements:")
print(instruccions,"\n")
print(informe)
