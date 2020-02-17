#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import cgi
import locale
import math
import json
import requests

if os.getenv("LANG") != "fr_FR.UTF-8":
    os.putenv("LANG", "fr_FR.UTF-8")
    os.execv(sys.argv[0], sys.argv)

def distance(x1, y1, x2, y2):
    x = (x2 - x1) / 90.0 * 10000.0 * 1000.0
    y = (y2 - y1) / 90.0 * 10000.0 * 1000.0
    return math.sqrt(x*x + y*y)

def get_distance(subway_entrance):
    return subway_entrance['distance']

def print_header():
    page_title = "Métro Stories"
    print("Content-type: text/html; charset=utf-8\r\n\r\n")
    print("<!doctype html>")
    print('<html lang="fr"><head><title>%s</title></head>' % page_title)
    print("<body>")
    print("<h1>%s</h1> " % page_title)

def print_footer():
    print("</body></html>")

def print_text(inline, text):
    if inline:
        print(text)
    else:
        print("<p>%s</p>" % text)

# Prints the search form
# inline is True if the form is inline, False otherwise
# label is the label for the text field
def print_search_form(inline, label):
    print('<form method="get">')
    print_text(inline, '<label for="address">%s</label>' % label)
    print_text(inline, '<input type="text" name="address" id="address"/>')
    value = "Lancer la recherche de bouches de métro autour de cette adresse"
    print_text(inline, '<input type="submit" value="%s"/>' % value)
    print("</form>")

def print_initial_content():
    print("<h2>Saisie des informations</h2>")
    print("<p>Recherchez les bouches de métro les plus proches d'une addresse en île de France.</p>")
    print_search_form(False, "Chercher les bouches de métro autour du: ")

def address_not_found(msg):
    print("<p>%s</p>" % msg)
    print("<p>Vous pouvez saisir une nouvelle adresse. Par exemple, 2 rue Simone Iff 75012 Paris</p>")
    print_search_form(False, "Nouvelle adresse: ")

def print_results(address):
    print("<h2>Résultats de votre recherche</h2>")
    response = requests.get('https://api-adresse.data.gouv.fr/search/?q=%s' % address)
    if not response:
        address_not_found("Impossible de déterminer les coordonnées GPS de l'adresse indiquée")
        return

    json_response = response.json()

    if not "features" in json_response:
        address_not_found("La réponse ne contient pas les informations attendues")
        return

    features = json_response['features']
    if len(features) < 1:
        address_not_found("Pas d'adresse dans la réponse")
        return

    if len(features) > 1:
        address_not_found("Il semble que plusieurs adresses correspondent à votre recherche. Ce cas n'est pas encore traité.")
        return

    full_address = features[0]
    geometry = full_address['geometry']
    position = geometry['coordinates']
    current_longitude = position[0]
    current_latitude = position[1]

    with open('/home/seb/site/ms/subway-entrances.json') as json_file:
        subway_entrances = json.load(json_file)
        json_file.close()

    for subway_entrance in subway_entrances:
        subway_entrance_latitude = subway_entrance['latitude']
        subway_entrance_longitude = subway_entrance['longitude']
        subway_entrance['distance'] = distance(current_latitude, current_longitude, subway_entrance_latitude, subway_entrance_longitude)

    subway_entrances.sort(key=get_distance)

    print("<p>Voici les 5 bouches de métro les plus proches de l'adresse indiquée (%s):</p>" % address)
    print("<p><ul>")
    for i in range(0, 5):
        n = subway_entrances[i]['name']
        d = int(round(subway_entrances[i]['distance']))
        print("<li>%s, à %d mètres</li>" % (n, d))
    print("</ul></p>")

def print_main_content():
    form = cgi.FieldStorage()
    if form.getvalue('address') == None:
        print_initial_content()
    else:
        print_results(form.getvalue('address'))

def main():
    locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
    print_header()
    print_main_content()
    print_footer()

main()
