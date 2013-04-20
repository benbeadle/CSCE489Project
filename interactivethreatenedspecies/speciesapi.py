"""
This file runs on /_ah/api/speciesapi/v[0-9]/*

These are the API methods that get called when clients use the Endpoints API

Version: 2.0
"""
import logging, csv, json, memcachepickler
from google.appengine.ext import endpoints
from protorpc import remote
from speciesapimessages import *
from google.appengine.api import memcache
from collections import defaultdict
from google.appengine.api.taskqueue import taskqueue, Task

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
#Returns the list of all the animal names.
def get_animal_list():
    animal_list = memcachepickler.get("animal_list")
    if animal_list is not None:
        return animal_list
    
    #So the animal list isn't in cache, go ahead and add to the queue to save it back up if it's not already being processed
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
    
    country_list = get_country_list()
    query = request.q
    
    if query == "" or query == None:
        return SearchCountriesResponse(countries=country_list)
    
    
    matching = {}
    for country in country_list:
        ind = country.name.lower().find(query.lower())
        if ind != -1:
            matching[country] = ind
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
    
    sm = memcache.get("search_animal|" + query)
    if sm is not None:
        return SearchAnimalsResponse(animals=sm)
    
    animal_list = get_animal_list()
    logging.info("animal_list len: " + str(len(animal_list)))
    matching = {}
    for animal in animal_list:
        ind = animal["name"].lower().find(query.lower())
        if ind != -1:
            matching[AnimalResult(name=animal["name"],type=animal["type"])] = ind
    #Sort the results by index
    matching_sorted = sorted(matching.iteritems(), key=lambda (k,v): (v,k))
    #logging.info(matching_sorted[0])
    #return
    results = [animal[0] for animal in matching_sorted][:10]
    memcache.set("search_animal|" + query, results)
    #results=[]
    return SearchAnimalsResponse(animals=results[:10])
  
  #Called on page load to prepare for the cache
  @endpoints.method(PageLoadRequest, PageLoadResponse, name='page.load', path='page/load', http_method='GET')
  def page_load(self, request):
    
    if (m("country_list") is None or m("animal_list") is None) and (m("queue_cache") != "running"):
        task = Task(url='/queue/cacher').add(queue_name='cacher')
        return PageLoadResponse(result=True)
    
    return PageLoadResponse(result=False)
  
#Create the service
speciesapi_service = endpoints.api_server([SpeciesApi], restricted=False)