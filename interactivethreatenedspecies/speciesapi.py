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
    country_list = m("country_list")
    if country_list is not None:
        return country_list
    
    #So the country list isn't in cache, go ahead and add to the queue to save it back up if it's not already being processed
    
    if m("queue_cache") != "running":
        task = Task(url='/queue/cacher').add(queue_name='cacher')
    
    return []
   
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
    
    cl = ndbpickler.get("country_list")
    matching = {}
    for code in cl:
        ind = cl[code].lower().find(query.lower())
        if ind != -1:
            matching[Country(name=cl[code], code=code)] = ind
    
    #Sort the results by index
    matching_sorted = sorted(matching.iteritems(), key=lambda (k,v): (v,k))
    results = [country[0] for country in matching_sorted]
    
    return SearchCountriesResponse(countries=results)
  
  #Search for animals
  @endpoints.method(SearchAnimalsRequest, SearchAnimalsResponse, name='search.animals', path='search/animals', http_method='GET')
  def search_animals(self, request):
    
    query = request.q
    
    if query == "" or query == None:
        return SearchAnimalsResponse(animals=[])
    
    def rang(input):
        letter = input[0].lower()
        if letter in ["a", "b", "c", "d"]:
            return "a-d"
        elif letter in ["e", "f", "g", "h"]:
            return "e-h"
        elif letter in ["i", "j", "k", "l"]:
            return "i-l"
        elif letter in ["m", "n", "o", "p"]:
            return "m-p"
        elif letter in ["q", "r", "s", "t"]:
            return "q-t"
        elif letter in ["u", "v", "w", "x", "y", "z"]:
            return "u-z"
    
    animal_list = ndbpickler.get("animal_list_" + rang(query))
    matching = {}
    for type in animal_list:
        type_upper = type.upper()
        for animal in animal_list[type]:
            ind = animal.lower().find(query.lower())
            if ind != -1:
                matching[AnimalResult(name=animal,type=type_upper)] = ind
    
    matching_sorted = sorted(matching.iteritems(), key=lambda (k,v): (v,k))
    results = [animal[0] for animal in matching_sorted][:10]
    
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

    memcache.set('task|' + task_id, {'status': 'pending'})
    return StatsInitResponse(task_id=task_id)
  
  #Get the results of the stats analyzation
  @endpoints.method(StatsStatusRequest, StatsStatusResponse, name='stats.status', path='stats/status', http_method='GET')
  def stats_status(self, request):
    
    result = memcache.get('task|' + request.task_id)
    if result is None:
        result = {'status': 'unknown'}
    
    #if result["status"] != "complete":
    return StatsStatusResponse(status=result['status'])
    
  
  """
  #Search the database for stats
  @endpoints.method(SearchDatabaseRequest, SearchDatabaseResponse, name='search.data', path='search/data', http_method='GET')
  def search_database(self, request):
    
    datas = json.loads('[{"code": "AE","name": "United Arab Emirates"},{"code": "GB","name": "United Kingdom"},{"code": "US","name": "United States"},{"code": "UM","name": "United States Minor Outlying Islands"},{"code": "HU","name": "Hungary"}]')
    
    ret_val = [Country(name=data["name"],code=data["code"], rating=randint(1,100)) for data in datas]
    
    return SearchDatabaseResponse(countries=ret_val)
  """
#Create the service
speciesapi_service = endpoints.api_server([SpeciesApi], restricted=False)