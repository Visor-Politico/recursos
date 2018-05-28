import tweepy
import json
import time
import os
import datetime
import csv
import sys
from collections import Counter
from fuzzywuzzy import fuzz


####Credenciales para uso del tweepyconsumer_key = ''

consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth,wait_on_rate_limit=True)

#Abrimos el json con toda la informacion
path_to_json = '../visor-politico/public/json/senado.json'
if os.path.isfile(path_to_json) and os.access(path_to_json, os.R_OK):
    jsonData = json.load(open(path_to_json))
else:
    with open(path_to_json, 'w') as outfile:
        js = {}
        json.dump(js, outfile)
    jsonData = json.load(open(path_to_json))
#En jsonData tenemos toda la informacion obtenida hasta la fecha

#Abrimos el archivo csv donde esta toda la informacion de los candidatos
#Nombre del archivo
file_name = "senado.csv"

#Abrimos el archivo como una lista de listas.
with open(file_name, 'rU') as f:
    reader = csv.reader(f)
    csvData = list(list(rec) for rec in csv.reader(f, delimiter=','))

#Removemos la cabezera
candidatos = csvData[1:]
#En candidatos tenemos la informacion de todos los candidatos que hay en el csv

#Este es el formato del csv. Se declaran las siguientes variables para facilitar el acceso a la lista de listas de candidatos
#Formato: actor politico, nombre, twitter

actor_politico = 0
nombre = 1
twitter = 2

#Abrimos el archivo csv que contiene las palabras clave que vamos a buscar.
key_words = 'keyWords.csv'
with open(key_words, 'rU') as f:
    reader_words = csv.reader(f)
    csvData_words = list(list(rec) for rec in csv.reader(f, delimiter=','))[0]
#En csvData_words tenemos la lista de palabras

#Llaves que manejamos en el json
#Las llaves tipo array son informacion que se usa en graficas de tipo continuas
#Las llaves de tipo objecto son llaves que se cambian en su totalidad cada semana
keys_array = ["seguidores","tweets","tweets_semana","palabras_clave"]
keys_object = ["data"]


#Si existe un usuario en el json pero no en el csv, es decir que ha sido removido del csv entonces lo borramos del json.
candidatos_nombres = []
for candidato in candidatos:
    candidatos_nombres.append(candidato[nombre])

for key_candidato in list(jsonData):
    if not key_candidato in candidatos_nombres:
        jsonData.pop(key_candidato)


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

#Variables para calcular fechas
dias_chequeo = 7
_now = datetime.datetime.now()
_date = (datetime.date.today() - datetime.timedelta(days=dias_chequeo))
now = time.mktime(datetime.datetime(_now.year, _now.month , _now.day).timetuple()) * 1000


def cuentaPalabrasClave(tweets):
    cnt = [0] * len(csvData_words)
    counts = Counter([item for sublist in [x.split() for x in [x.text for x in tweets]] for item in sublist])
    for element in counts:
        for idx,word in enumerate(csvData_words):
            if fuzz.ratio(element, word) > 79:
                cnt[idx] += counts[element]
                break
    return cnt
    #return [counts[key] for key in csvData_words]

#Checamos todos los candidatos
for candidato in candidatos:
    #Si el candidato tiene twitter
    if candidato[twitter]:
        #Checamos si el twitter es valido
        try:
            user = api.get_user(candidato[twitter])
        except:
            #De no ser valido mandamos un mensaje de que el usuario tiene un twitter inexistente
            print("Error, el usuario " + candidato[nombre] + " contiene un twitter :" + candidato[twitter] + " inexistente, favor de corregir")
            jsonData[candidato[nombre]]["data"] = {
                "actor_politico": candidato[actor_politico],
                "twitter": candidato[twitter],
                "followers": 0,
                "picture": "../img/no_image.png",
                "tweets": 0
            }
            continue
        #Si el usuario tiene un twitter existente llenamos la informacion estatica
        jsonData[candidato[nombre]]["data"] = {
            "actor_politico": candidato[actor_politico],
            "name": user.name,
            "twitter": candidato[twitter],
            "followers": user.followers_count,
            "picture": user.profile_image_url.replace("_normal",""),
            "tweets": user.statuses_count
        }
        #Contador utilizado para contar el numero de tweets en dias de chequeo
        count = 0
        #Fecha hace dias de chequeo
        startDate = datetime.datetime(_date.year, _date.month, _date.day, 0, 0, 0)
        #Arreglo donde se van guardando los tweets para despues medir la longitud de ese arreglo
        tweets = []
        #Condicion que se utiliza para ver si hemos o no pasado la fecha establecida de dias de chequeo
        cond = True
        #La api nos permite checar 20 tweets por pagina, asi que utilizamos una variable page para ir checando todas las paginas hasta que obtengamos los tweets necesarios
        page = 0
        #Debido a fallas de la api tweepy, extraemos un gran numero de tweets y vamos checando por fechas hasta que llegamos a una fecha que ya no entre en el rango de startDate

        while cond:
            page += 1
            #Obtenemos los tweets en la pagina page
            tmpTweets = api.user_timeline(user.id, page=page)
            #Checamos esos tweets y vemos si estan dentro del intervalo de fechas correcto
            for tweet in tmpTweets:
                #Si si entran en el rango los agregamos
                if tweet.created_at > startDate:
                    count +=1
                    tweets.append(tweet)
                else:
                    #De no entrar cambiamos la condicion a falso y rompemos el ciclo
                    cond = False
                    break
        #Agregamos la informacion del dia de hoy
        #Seguidores al dia de hoy
        jsonData[candidato[nombre]]["seguidores"].append([
            now,
            user.followers_count
        ])
        #Tweets al dia de hoy
        jsonData[candidato[nombre]]["tweets"].append([
            now,
            user.statuses_count
        ])
        #Numero de tweets de hace dias de chequeo
        jsonData[candidato[nombre]]["tweets_semana"].append([
            now,
            count
        ])
        #Numero de palabras clave

        jsonData[candidato[nombre]]["palabras_clave"] = [cuentaPalabrasClave(tweets)]

    #Si el candidato no tiene twitter, llenamos su informacion basica publica y aclaramos que no tiene twitter
    else:
        jsonData[candidato[nombre]]["data"] = {
            "actor_politico": candidato[actor_politico],
            "twitter": candidato[twitter],
            "followers": 0,
            "picture": "../img/no_image.png",
            "tweets": 0
        }

#Limpiamos el json para borrar fechas repitidas

def unique_by_first_n(n, coll):
    seen = set()
    for item in coll:
        compare = tuple(item[:n])    # Keep only the first `n` elements in the set
        if compare not in seen:
            seen.add(compare)
            yield item

for _key in jsonData:
    for element in jsonData[_key]:
        if type(jsonData[_key][element]) is list and element != 'palabras_clave':
            jsonData[_key][element] = list(unique_by_first_n(1,jsonData[_key][element]))
            jsonData[_key][element].sort(key=lambda x: x[0])


with open(path_to_json, 'w') as outfile:
    json.dump(jsonData, outfile)
