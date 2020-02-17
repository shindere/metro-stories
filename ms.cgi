#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Finds the nearest subway entrances"""

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

def distance(x_1, y_1, x_2, y_2):
    """Computes the distance between two GPS locations, in meters"""
    x_0 = (x_2 - x_1) / 90.0 * 10000.0 * 1000.0
    y_0 = (y_2 - y_1) / 90.0 * 10000.0 * 1000.0
    return math.sqrt(x_0 * x_0 + y_0 * y_0)

def get_distance(subway_entrance):
    """Returns the distance between a subway entrance and the reference point"""
    return subway_entrance['distance']

def print_header():
    """Prints the header of the web page"""
    page_title = "Métro Stories"
    print("Content-type: text/html; charset=utf-8\r\n\r\n")
    print("<!doctype html>")
    print('<html lang="fr"><head><title>%s</title></head>' % page_title)
    print("<body>")
    print("<h1>%s</h1> " % page_title)

def print_footer():
    """Prints the footer of the web page"""
    print("</body></html>")

def print_text(inline, text):
    """Prints a text, either in a paragraph if inline is False, or as is if inline is True"""
    if inline:
        print(text)
    else:
        print("<p>%s</p>" % text)

def print_search_form(inline, label):
    """Prints an address search form with the provided label"""
    print('<form method="get">')
    print_text(inline, '<label for="address">%s</label>' % label)
    print_text(inline, '<input type="text" name="address" id="address"/>')
    value = "Lancer la recherche de bouches de métro autour de cette adresse"
    print_text(inline, '<input type="submit" value="%s"/>' % value)
    print("</form>")

def print_initial_content():
    """Prints the main content of the initial search page"""
    print("<h2>Saisie des informations</h2>")
    print("<p>Recherchez les bouches de métro les plus proches d'une "
          "addresse en île de France.</p>")
    print_search_form(False, "Chercher les bouches de métro autour du: ")

def address_not_found(msg):
    """Prints a message explaining why the address was not found and a new search form"""
    print("<p>%s</p>" % msg)
    print("<p>Vous pouvez saisir une nouvelle adresse. "
          "Par exemple, 2 rue Simone Iff 75012 Paris</p>")
    print_search_form(False, "Nouvelle adresse: ")

def lookup_address(address):
    """Looks up the given address for GPS coordinates in national address DB"""
    response = requests.get('https://api-adresse.data.gouv.fr/search/?q=%s' % address)
    if not response:
        address_not_found("Impossible de déterminer les coordonnées GPS de l'adresse indiquée")
        return []

    json_response = response.json()

    if not "features" in json_response:
        address_not_found("La réponse ne contient pas les informations attendues")
        return []

    features = json_response['features']
    if len(features) < 1:
        address_not_found("Pas d'adresse dans la réponse")
        return []
    return features

def load_subway_entrances(file_name):
    """Loads the subway entrances from a JSON file"""
    with open(file_name) as json_file:
        subway_entrances = json.load(json_file)
        json_file.close()
    return subway_entrances

def find_nearest_subway_entrances(current_latitude, current_longitude):
    """Finds the nearest subway entrances to the given location"""
    subway_entrances = load_subway_entrances('/home/seb/site/ms/subway-entrances.json')

    for subway_entrance in subway_entrances:
        subway_entrance_latitude = subway_entrance['latitude']
        subway_entrance_longitude = subway_entrance['longitude']
        subway_entrance['distance'] = distance(
            current_latitude, current_longitude,
            subway_entrance_latitude, subway_entrance_longitude)

    subway_entrances.sort(key=get_distance)
    return subway_entrances

def print_subway_entrances(address, number, subway_entrances):
    """Prints the given number of subway entrances"""
    print("<p>Voici les %d bouches de métro les plus proches de l'adresse "
          "indiquée (%s):</p>" % (number, address))
    print("<p><ul>")
    for i in range(0, number):
        entrance_name = subway_entrances[i]['name']
        entrance_distance = int(round(subway_entrances[i]['distance']))
        print("<li>%s, à %d mètres</li>" % (entrance_name, entrance_distance))
    print("</ul></p>")

def print_address_link(address):
    """Print link to an address"""
    location = address['geometry']['coordinates']
    latitude = location[1]
    longitude = location[0]
    label = address['properties']['label']
    print('<a href="?address=%s&latitude=%s&longitude=%s">%s</a>' %
          (label, latitude, longitude, label))

def print_addresses_links(addresses):
    """Print list of found addresses"""
    print("<p>Plusieurs adresses correspodnent à votre recherche. "
          "Sélectionnez-en une dans la liste ci-dessous ou saisissez-en "
          "une autre:</p>")
    print("<ul>")
    for address in addresses:
        print("<li>")
        print_address_link(address)
        print("</li>")
    print("<li>")
    print_search_form(True, "Autre adresse: ")
    print("</li>")
    print("</ul>")

def print_results(form):
    """Prints the results of a search"""
    print("<h2>Résultats de votre recherche</h2>")
    address = form.getvalue('address')
    current_latitude = 0.0
    current_longitude = 0.0
    if form.getvalue('latitude') is None or form.getvalue('longitude') is None:
        addresses = lookup_address(address)
        if addresses == []:
            return

        if len(addresses) > 1:
            print_addresses_links(addresses)
            return

        full_address = addresses[0]
        geometry = full_address['geometry']
        position = geometry['coordinates']
        current_longitude = position[0]
        current_latitude = position[1]
    else:
        current_latitude = float(form.getvalue('latitude'))
        current_longitude = float(form.getvalue('longitude'))

    subway_entrances = find_nearest_subway_entrances(current_latitude, current_longitude)
    print_subway_entrances(address, 5, subway_entrances)

def print_main_content(form):
    """Prints the main ocntent: either a search form, or the search results"""
    if form.getvalue('address') is None:
        print_initial_content()
    else:
        print_results(form)

def main():
    """The main function of the script"""
    locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
    form = cgi.FieldStorage()
    print_header()
    print_main_content(form)
    print_footer()

main()
