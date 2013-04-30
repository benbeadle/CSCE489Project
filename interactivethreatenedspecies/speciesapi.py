"""
This file runs on /_ah/api/speciesapi/v[0-9]/*

These are the API methods that get called when clients use the Endpoints API

Version: 2.0
"""
import logging, csv, json, ndbpickler, time, md5
from google.appengine.ext import endpoints
from protorpc import remote
from speciesapimessages import *
from google.appengine.api import memcache
from collections import defaultdict
from google.appengine.api.taskqueue import taskqueue, Task
from random import randint

def m(t):
    return memcache.get(t)
def l(out):
    logging.info(out)

    
#Returns the list of all the countries.
def get_country_list():
    #country_list = ndbpickler.get("country_list")
    #if False and country_list is not None:
    #    return country_list
    f = open("country_list.json")
    countries = json.loads(f.read())
    f.close()
    #ndbpickler.set("country_list", countries)
    return countries
#Returns the subset of animals.
def get_animal_list(query):
    def rang(input):
        letter = input[0].lower()
        letter_ord = ord(letter)
        if letter_ord % 2 == 1:
            r = letter + "-" + chr(letter_ord+1)
        else:
            r = chr(letter_ord-1) + "-" + letter
        return r
    
    the_let_range = rang(query)
    animal_list = ndbpickler.get("animal_list_" + the_let_range)
    if animal_list is not None:
        return animal_list
    
    
    f = open("animal_list.json")
    animals = json.loads(f.read())
    f.close()
    results = {}
    
    for letters in animals:
        if letters is not None:
            ndbpickler.set("animal_list_" + letters, animals[letters])
            if the_let_range == letters:
                results = animals[letters]
    return results
   
#Define the species API
@endpoints.api(name='speciesapi',version='v2',
               description="Endangered species API", hostname='interactivethreatenedspecies.appspot.com')
#The API Class
class SpeciesApi(remote.Service):
  
  #Search for countries
  @endpoints.method(SearchCountriesRequest, SearchCountriesResponse, name='search.countries', path='search/countries', http_method='GET')
  def search_countries(self, request):
    
    query = request.q
    
    if query == "" or query == None:
        return SearchCountriesResponse(countries=[])
    
    cl = get_country_list()
    matching = {}
    for country in cl:
        ind = country.lower().find(query.lower())
        if ind != -1:
            matching[Country(name=country, code=cl[country])] = ind
    
    #Sort the results by index
    matching_sorted = sorted(matching.iteritems(), key=lambda (k,v): (v,k))
    results = [country[0] for country in matching_sorted]
    
    return SearchCountriesResponse(countries=results)
  
  #Search for animals
  @endpoints.method(SearchAnimalsRequest, SearchAnimalsResponse, name='search.animals', path='search/animals', http_method='GET')
  def search_animals(self, request):
    
    query = request.q.lower()
    
    if query == "" or query == None:
        return SearchAnimalsResponse(animals=[])
    
    animal_list = get_animal_list(query)
    
    matching = {}
    for type in animal_list:
        type_upper = type.upper()
        for animal in animal_list[type]:
            ind = animal.lower().find(query)
            if ind != -1:
                matching[AnimalResult(name=animal,type=type_upper)] = ind
    
    matching_sorted = sorted(matching.iteritems(), key=lambda (k,v): (v,k))
    results = [animal[0] for animal in matching_sorted[:10]]
    logging.info("Results: {0}".format(len(results)))
    return SearchAnimalsResponse(animals=results)
  
  #Begin the stats analyzation
  @endpoints.method(StatsInitRequest, StatsInitResponse, name='stats.init', path='stats/init', http_method='GET')
  def stats_init(self, request):
    
    query = request.q
    
    if query == "" or query == None:
        return StatsInitResponse(task_id="")
    
    task_id = str(md5.new(str(time.time())).hexdigest())
    task = Task(url='/queue/stats', params={'task_id': task_id, 'q': query}, name=task_id)
    task.add(queue_name='stats')

    memcache.set('task|' + task_id, {'status': 'pending'}, 3600)
    return StatsInitResponse(task_id=task_id)
  
  #Get the results of the stats analyzation
  @endpoints.method(StatsStatusRequest, StatsStatusResponse, name='stats.status', path='stats/status', http_method='GET')
  def stats_status(self, request):
    
    result = m('task|' + request.task_id)
    if result is None:
        result = {'status': 'unknown'}
    
    countries = []
    common = []
    native = []
    if "countries" in result:
        country_codes = get_country_list()
        for c in result["countries"]:
            code = country_codes[c.lower()] if c.lower() in country_codes else ""
            countries.append(Country(name=c,code=code,rating=result["countries"][c]))
        for c in result["countries"].most_common(10):
            code = country_codes[c[0].lower()] if c[0].lower() in country_codes else ""
            common.append(Country(name=c[0],code=code,rating=c[1]))
        for c in result["native"].most_common(10):
            code = country_codes[c[0].lower()] if c[0].lower() in country_codes else ""
            native.append(Country(name=c[0],code=code,rating=c[1]))
    specie_count = result["specie_count"] if "specie_count" in result else 0
    return StatsStatusResponse(status=result['status'], countries=countries, specie_count=specie_count,common_countries=common,native_countries=native)
    
#Create the service
speciesapi_service = endpoints.api_server([SpeciesApi], restricted=False)