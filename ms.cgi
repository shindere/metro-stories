#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, sys
lang = os.getenv("LANG")
if lang != "fr_FR.UTF-8":
    os.putenv("LANG","fr_FR.UTF-8")
    os.execv(sys.argv[0], sys.argv)
    
import cgi
import locale

def print_header():
  page_title = "Métro Story"
  print("Content-type: text/html; charset=utf-8\r\n\r\n")
  locale.setlocale(locale.LC_ALL,"fr_FR.UTF-8")
  print('<html lang="fr"><head><title>%s</title></head>' % page_title)
  print("<body>")
  print("<h1>%s</h1> " % page_title)

def print_footer():
  print("</body></html>")

def print_search_form():
  print("<p>Recherchez les bouches de métro les plus proches d'une addresse en île de France.</p>")
  print('<form method="post">')
  print('<p><label for="q">Chercher les bouches de métro autour du: </label></p>')
  print('<p><input type="text" name="q" id="q"/></p>')
  print('<p><input type="submit" value="Lancer la recherche de bouches de métro autour de cette adresse"/></p>')
  print("</form>")

def print_results(address):
  print("<p>Bouches situées autour du " + address + "</p>")

def print_main_content():
  form = cgi.FieldStorage()
  if form.getvalue('q') == None:
    print_search_form()
  else:
    print_results(form.getvalue('q'))



def main():
  print_header()
  print_main_content()
  print_footer()

main()
