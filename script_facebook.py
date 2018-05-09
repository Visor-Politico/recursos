#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 21:46:21 2018

@author: ericklf
"""

import csv
import os
import json
import time
import datetime
import requests

#Llamada para obtener los datos
def request_facebook(req):
    r = requests.get("https://graph.facebook.com/v2.10/" + req , {"access_token" : "EAACEdEose0cBALZCnl2WkToCXky0mMCZAqGEZBiSUbzURq4qknfUHePZCtiX826z4PR2ZAB55P8onKgrSlCXTZACHPdYlBfYKc426vY2r2C7IeG3ycN5H6rZBmLUEMyP7BL9J8Q3Mgu3xLSDvD14ctFPdOUcczeoUKk9ZCYWZCKToaWxKXDlZBMeiswZAZCGSqIa7WYZD"})
    return r
#definimos el nombre del archivo donde guardaremos los datos de los candidatos
path_to_json = '../visor-politico/public/json/Data2.json'
if os.path.isfile(path_to_json) and os.access(path_to_json, os.R_OK):
    jsonData = json.load(open(path_to_json))
else:
    with open(path_to_json, 'w') as outfile:
        js = {}
        json.dump(js, outfile)
    jsonData = json.load(open(path_to_json))
    
#Abrimos el archivo csv donde esta toda la informacion de los candidatos
#Nombre del archivo
file_name = "candidatos.csv"
#Abrimos el archivo como una lista de listas.
with open(file_name, 'rU') as f:
    reader = csv.reader(f)
    csvData = list(list(rec) for rec in csv.reader(f, delimiter=','))

#Removemos la cabezera
candidatos = csvData[1:]
#En candidatos tenemos la informacion de todos los candidatos que hay en el csv​
#Este es el formato del csv. Se declaran las siguientes variables para facilitar el acceso a la lista de listas de candidatos
#Formato: #,Actor Politico, sede, cargo, nombre aspirante, genero, twitter
numero = 0
actor_politico = 1
sede = 2
cargo = 3
nombre = 4
genero = 5
twitter = 6
facebook = 7
key_words = 'keyWords.csv'
with open(key_words, 'rU') as f:
    reader_words = csv.reader(f)
    csvData_words = list(list(rec) for rec in csv.reader(f, delimiter=','))[0]
#En csvData_words tenemos la lista de palabras​
#Llaves que manejamos en el json
#Las llaves tipo array son informacion que se usa en graficas de tipo continuas
#Las llaves de tipo objecto son llaves que se cambian en su totalidad cada semana
keys_array = ["seguidores","comentarios"]
keys_object = ["data"]

#Variables para calcular fechas
dias_chequeo = 7
_now = datetime.datetime.now()
_date = (datetime.date.today() - datetime.timedelta(days=dias_chequeo))
now = time.mktime(datetime.datetime(_now.year, _now.month , _now.day).timetuple()) * 1000

#Validacion del csv con nuestro json
#Checamos los candidatos en nuestro csv con los que tenemos en el json
for candidato in candidatos:
    #Si encontramos un candidato nuevo en el csv lo agregamos al json
    if not candidato[nombre] in jsonData:
        jsonData[candidato[nombre]] = {}
        #Le agregamos todas las llaves que tenemos registradas
        for key in keys_array:
            jsonData[candidato[nombre]][key] = []
        for key in keys_object:
            jsonData[candidato[nombre]][key] = {}
    #Si el candidato esta en ambos, el csv y el json solo checamos sus atributos, por si se agrego un nuevo atributo.
    elif candidato[nombre] in jsonData:
        for key in keys_array:
            if key not in jsonData[candidato[nombre]]:
                jsonData[candidato[nombre]][key] = []
        for key in keys_object:
            if key not in jsonData[candidato[nombre]]:
                jsonData[candidato[nombre]][key] = {}

#Checamos todos los candidatos
for candidato in candidatos:
    #Si el candidato tiene twitter
    if candidato[facebook]:
        #Checamos si el facebook es valido
        req = ""+candidato[facebook]+"?fields=id,name,fan_count,picture"
        r = request_facebook(req).json()
        if('error' in r):
            print("Error, el usuario " + candidato[nombre] + " contiene un facebook :" + candidato[facebook] + " inexistente, favor de corregir")
            jsonData[candidato[nombre]]["data"] = {
                "actor_politico": candidato[actor_politico],
                "sede": candidato[sede],
                "cargo": candidato[cargo],
                "genero": candidato[genero],
                "facebook": candidato[facebook],
                "followers": 0,
                "picture": "../img/no_image2.png"
            }
        else:
            #Si el usuario tiene una pagina de facebook existente llenamos la informacion estatica
            jsonData[candidato[nombre]]["data"] = {
                "actor_politico": candidato[actor_politico],
                "sede": candidato[sede],
                "cargo": candidato[cargo],
                "name": r['name'],
                "genero": candidato[genero],
                "facebook": candidato[facebook],
                "followers": r['fan_count'],
                "picture": r['picture']['data']['url']
                #"comentarios": 0
            }
            jsonData[candidato[nombre]]["seguidores"].append([
                now,
                r['fan_count']
            ])
            #Si el candidato no tiene twitter, llenamos su informacion basica publica y aclaramos que no tiene twitter
    else:
        jsonData[candidato[nombre]]["data"] = {
            "actor_politico": candidato[actor_politico],
            "sede": candidato[sede],
            "cargo": candidato[cargo],
            "genero": candidato[genero],
            "facebook": candidato[facebook],
            "followers": 0,
            "picture": "../img/no_image2.png",
            #"comentarios": 0
        }

with open(path_to_json, 'w') as outfile:
    json.dump(jsonData, outfile)
