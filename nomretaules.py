# ajuda a la traducció dels noms dels retaules ceràmics de les llistes
# -crea: fa un document de text amb una llista dels noms de les llistes object
# o l'afegeix al document existent. En aquest document s'haurien d'introduir algunes traduccions
# separades de l'original amb un tabulador.
# -trad: llegeix les traduccions i les fa servir
# Es pot posar la traducció dels noms sencers o de trossos.
# La gràcia és que alguns noms es repeteixen molt.

import pywikibot as pwb
from pywikibot import pagegenerators
import mwparserfromhell
#from collections import Counter
#import math
import re
import sys

def nomsretaule(pllista, trad=False, dicc={}):
    noms=[]
    origen=pllista.title()
    text=pllista.get()
    text0=text
    code = mwparserfromhell.parse(text)
    t=code.filter_templates();
    #print(t)
    codiclau = []
    sumariredir = ""
    for template in t:
        if template.has("nom"):
            tradposa=""
            nom=template.get("nom").value.strip()
            if nom in dicc.values():
                print("JA CONEGUT:",nom)
                continue
            print(nom)
            if trad and nom in dicc.keys():
                tradposa = dicc[nom]
                template.add("nom", tradposa)
            else:
                noms.append(nom)
            if tradposa=="":
                davant = re.sub("(.*)(en (la )?(calle|plaza|avenida).*)",r"\1",nom).strip()
                darrera = re.sub(".*(en (la )?(calle|plaza|avenida).*)",r"\1",nom).strip()
                if nom == davant+" "+darrera:
                    if davant in dicc.keys() and darrera in dicc.keys():
                        tradposa= dicc[davant]+" "+dicc[darrera]
                        template.add("nom", tradposa)
                    else:
                        noms = noms + [davant, darrera]
            if tradposa=="":        
                davant = re.sub("(.*)(, [Cc]/.*)",r"\1",nom)
                darrera = re.sub("(.*)(, [Cc]/.*)",r"\2",nom)
                print(davant)
                print(darrera)
                if nom == davant+darrera:                        
                    if davant in dicc.keys() and darrera in dicc.keys():
                        tradposa= dicc[davant]+" "+dicc[darrera]
                        template.add("nom", tradposa)
                    else:
                        noms = noms + [davant, darrera]
            if tradposa=="":        
                davant = re.sub("(.*)(en (la )?(calle|plaza|avenida).*) ([0-9]+)",r"\1",nom).strip()
                darrera = re.sub("(.*)(en (la )?(calle|plaza|avenida).*) ([0-9]+)",r"\2",nom).strip()
                num = re.sub("(.*)(en (la )?(calle|plaza|avenida).*) ([0-9]+)",r"\5",nom).strip()
                if nom == davant+" "+darrera+" "+num:
                    if davant in dicc.keys() and darrera in dicc.keys():
                        tradposa= dicc[davant]+" "+dicc[darrera]+" "+num
                        template.add("nom", tradposa)
                    else:
                        noms = noms + [davant, darrera]
            if tradposa=="":        
                davant = re.sub("(.*)(, [Cc]/.*) ([0-9]+)",r"\1",nom)
                darrera = re.sub("(.*)(, [Cc]/.*) ([0-9]+)",r"\2",nom)
                num = re.sub("(.*)(, [Cc]/.*) ([0-9]+)",r"\3",nom)
                print(davant)
                print(darrera)
                if nom == davant+darrera:                        
                    if davant in dicc.keys() and darrera in dicc.keys():
                        tradposa= dicc[davant]+" "+dicc[darrera]
                        template.add("nom", tradposa)
                    else:
                        noms = noms + [davant, darrera]
        if trad and template.has("nomcoor"):
            nomcoor=template.get("nomcoor").value.strip()
            if nomcoor==nom and tradposa != "":
                template.add("nomcoor", tradposa)
            elif nomcoor in dicc.keys():
                template.add("nomcoor", dicc[nom])           
    text=code
    if text != text0:
        print("Desant",pllista)
        pllista.put(text, "Robot col·loca als noms dels retaules traduccions fetes a mà")
    else:
        print("cap canvi")
    return (noms)

def nomsretaules(nomorigen, trad=False, dicc={}):
    noms = []
    if re.match("llistes", nomorigen.casefold()):
        cat = pwb.Category(site,'Category:'+nomorigen)
        print(cat)
        llistes = pagegenerators.CategorizedPageGenerator(cat, recurse=True)
    else:
        llistes = [pwb.Page(site, nomorigen)]
    for llista in llistes:
        print(llista)
        noms=noms+nomsretaule(llista, trad, dicc)
    return(noms)

def desa(llista, nomfitx="C:\\Users\\Pere\\Documents\\perebot\\retaulestrad.txt"):
    text = "\n".join(llista).replace("\u200b", " ")
    try:
        f = open(nomfitx, "a")
    except FileNotFoundError:
        f = open(nomfitx, "w")
    f.write(text)
    f.close()
    return() 

def carrega_traduccions():
    try:
        f = open("C:\\Users\\Pere\\Documents\\perebot\\retaulestrad.txt", "r")
    except FileNotFoundError:
        print ("El fitxer de traduccions no existeix.")
        return({})
    dicc = {}
    for linia in f:
        #print(linia)
        if "\t" in linia:
            #print ("TE TRADUCCIÓ", linia)
            trossos = linia.split("\t")
            dicc[trossos[0].strip()]=trossos[-1].strip()
    f.close()
    return(dicc)

# el programa comença aquí
crea=False
trad=False
arguments = sys.argv[1:]
if len(arguments)>0:
    if "-crea" in arguments:
        crea=True
        arguments.remove("-crea")
    if "-trad" in arguments:
        trad=True
        arguments.remove("-trad")
if len(arguments)>0:
    nomllista=" ".join(arguments)
else:
    sys.exit("Manca el nom de la llista de monuments. Agafem opció per defecte") 
traduccio = carrega_traduccions()
#print (traduccio)
site=pwb.Site('ca')
noms=nomsretaules(nomllista, trad, traduccio)
noms.sort()
#print (noms)
if crea: 
    desa(noms)