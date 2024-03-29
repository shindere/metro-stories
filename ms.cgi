#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Finds the nearest subway entrances"""

import os
import sys
import re
import cgi
import locale
import math
import requests
import overpass

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

def cleanup_station_name(name):
    """Cleans up a station name by removing the "line" part"""
    return re.sub(r"\w*\(.*\)", "", name).rstrip()

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

def print_new_search_form(inline):
    """Prints a form to lookup a new address"""
    print("<p>Vous pouvez saisir une nouvelle adresse. "
          "Par exemple, 2 rue Simone Iff 75012 Paris</p>")
    print_search_form(inline, "Nouvelle adresse: ")

def print_initial_content():
    """Prints the main content of the initial search page"""
    print("<h2>Saisie des informations</h2>")
    print("<p>Recherchez les bouches de métro les plus proches d'une "
          "adresse.</p>")
    print_search_form(False, "Chercher les bouches de métro autour du: ")

def address_not_found(msg):
    """Prints a message explaining why the address was not found and a new search form"""
    print("<p>%s</p>" % msg)

def lookup_address(address):
    """Looks up the given address for GPS coordinates in national address DB"""
    response = requests.get('https://api-adresse.data.gouv.fr/search/?q=%s' % address)
    if not response:
        address_not_found("Impossible de déterminer les coordonnées GPS de l'adresse indiquée")
        return []

    json_response = response.json()

    if "features" not in json_response:
        address_not_found("La réponse ne contient pas les informations attendues")
        return []

    features = json_response['features']
    if len(features) < 1:
        address_not_found("Pas d'adresse dans la réponse")
        return []
    return features

def build_entrance_query(latitude, longitude, radius):
    """Builds the OverPass query to look for subway entrances around the given location"""
    return "node[railway=subway_entrance](around:%d,%f,%f);" % (radius, latitude, longitude)

def build_station_query(entrance_id):
    """Returns the OverPass query to find to which station an entrance belongs to"""
    return "node(id:%s);rel(bn)[type=public_transport][public_transport=stop_area];" % entrance_id

def find_station(subway_entrance):
    """Finds the name of the station to which an entrance belongs"""
    query = build_station_query(subway_entrance['id'])
    overpass_api = overpass.API()
    result = overpass_api.Get(query, responseformat='json')
    stations = result['elements']
    if stations is None or stations == []:
        return "inconnue (bouche orpheline, id=%s)" % subway_entrance['id']
    return cleanup_station_name(stations[0]['tags']['name'])

def find_nearest_subway_entrances(current_latitude, current_longitude):
    """Finds the nearest subway entrances to the given location"""
    query = build_entrance_query(current_latitude, current_longitude, 2000)
    overpass_api = overpass.API()
    result = overpass_api.Get(query, responseformat='json')
    subway_entrances = result['elements']
    for subway_entrance in subway_entrances:
        subway_entrance_latitude = subway_entrance['lat']
        subway_entrance_longitude = subway_entrance['lon']
        subway_entrance['distance'] = distance(
            current_latitude, current_longitude,
            subway_entrance_latitude, subway_entrance_longitude)

    subway_entrances.sort(key=get_distance)
    return subway_entrances

def entrance_number_is_valid(entrance_number):
    """Checks whether an entrance number is valid"""
    invalid_entrance_numbers = ("0", "-1", "?")
    return entrance_number is not None and entrance_number not in invalid_entrance_numbers

def print_subway_entrances(address, number, subway_entrances):
    """Prints the given number of subway entrances"""
    print("<p>Voici les %d bouches de métro les plus proches de l'adresse "
          "indiquée (%s):</p>" % (number, address))
    print("<p><ul>")
    for i in range(number):
        print_id = False
        station = find_station(subway_entrances[i])
        if subway_entrances[i]['tags'] is None or 'name' not in subway_entrances[i]['tags']:
            entrance_name = None
        else:
            entrance_name = subway_entrances[i]['tags']['name']
        if not entrance_name:
            entrance_name = "sans nom"
            print_id = True

        if subway_entrances[i]['tags'] is not None and 'ref' in subway_entrances[i]['tags']:
            entrance_number = subway_entrances[i]['tags']['ref']
        else:
            entrance_number = None
        if entrance_number_is_valid(entrance_number):
            entrance_number = "sortie %s" % entrance_number
        else:
            entrance_number = "numéro de sortie inconnu"
            print_id = True
        entrance_distance = int(round(subway_entrances[i]['distance']))
        idstr = ""
        if print_id:
            idstr = " (id=%s)" % subway_entrances[i]['id']
        print("<li>Station %s, %s, %s, à %d mètres%s</li>"
              % (station, entrance_number, entrance_name, entrance_distance, idstr))
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
    print("<p>Plusieurs adresses correspondent à votre recherche. "
          "Sélectionnez-en une dans la liste ci-dessous ou saisissez-en "
          "une autre:</p>")
    print("<ul>")
    for address in addresses:
        print("<li>")
        print_address_link(address)
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
        print_new_search_form(False)

def main():
    """The main function of the script"""
    locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")
    form = cgi.FieldStorage()
    print_header()
    print_main_content(form)
    print_footer()


if __name__ == '__main__':
    main()
