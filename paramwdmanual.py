# Ajuda per copiar manualment el paràmetre wikidata a les llistes de monuments
# Preparat per copiar i enganxar els BRL a les llistes valencianes a partir d'eswiki.
# L'únic paràmetre és el nom de la llista:
# python paramwdman.py "llista de monuments de l'Alt Maestrat"
# Les cometes són opcionals.

import pywikibot as pwb
import mwparserfromhell
import sys
import re

def actuallistaman(pllista):
    origen=pllista.title()
    text=pllista.get()
    text0=text
    code = mwparserfromhell.parse(text)
    t=code.filter_templates();
    #print(t)
    for template in t:
        posat = False
        if template.name.matches(("filera BIC Val")):
            if template.has("wikidata"):
                wd=template.get("wikidata").value.strip()
                wd=re.sub("<!-- no ([Ww][Dd] )?((auto|amb bot) )?-->", "", wd).strip()
                #print(wd)
            else:
                wd=""
            if wd=="" and template.has("prot"):
                if re.match("BRL|BIC", template.get("prot").value.strip()):
                    print (template.get("nomcoor").value.strip())
                    entrada = input("Wikidata: ")
                    if re.match("[Qq].+", entrada):
                        template.add("wikidata",entrada.upper().strip())
    text=code
    if text != text0:
        print("Desant",pllista)
        pllista.put(text,u"Robot actualitza manualment el paràmetre wikidata")
    else:
        print("Cap canvi")
    return()


# el programa comença aquí
arguments = sys.argv[1:]
if len(arguments)>0:
    nomllista=" ".join(arguments)
else:
    print("Manca el nom de la llista de monuments. Agafem opció per defecte")
    nomllista="Llista de monuments del Baix Maestrat"
site=pwb.Site('ca')
pag = pwb.Page(site, nomllista)
#pag = pwb.Page(site, "Usuari:PereBot/taller")
print (pag)
actuallistaman(pag)
