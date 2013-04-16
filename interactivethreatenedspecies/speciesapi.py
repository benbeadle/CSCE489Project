"""
This file runs on /_ah/api/speciesapi/v[0-9]/*

These are the API methods that get called when clients use the Endpoints API

Version: 1.0
"""
import logging, csv, json
from google.appengine.ext import endpoints
from protorpc import remote
from speciesapimessages import *
from google.appengine.api import memcache

def import_data():
    #Import the data from the exported file
    f = open("data.csv")
    reader = csv.reader(f)
    rows = []
    for row in reader:
        t = []
        for r in row:
            try:
                t.append(r.decode("UTF-8"))
            except:
                t.append(r)
        rows.append(t)
    f.close()
    return rows
def m(t):
    return memcache.get(t)
def l(out):
    logging.info(out)
#Returns the list of all the countries. Save it in memcache
def get_country_list():
    country_list = m("country_list")
    if country_list is not None:
        return country_list
    
    rows = import_data()
    headers = rows.pop(0)
    
    #Loop through the rows and get the data
    country_index = [index for index,h in enumerate(headers) if h.lower()=="countries"][0]
    country_list = []
    for row in rows:
        if row[country_index] == "N/A":
            continue
        countries = json.loads(row[country_index])
        for status in countries:
            #Some countries have their specific states. We don't care about that here
            country_list += [country.split(" (")[0] for country in countries[status]]
    country_list = list(set(country_list))
    memcache.set("country_list", country_list)
    return country_list
def get_code_list():
    code_list = m("code_list")
    if code_list is not None:
        return code_list
    
    f = open("ISOtoCountry.xls")
    reader = csv.reader(f)
    rows = [row for row in reader]
    f.close()
    
    memcache.set("code_list", rows)
    return rows

#Define the species API
@endpoints.api(name='speciesapi',version='v1',
               description="Endangered species API", hostname='interactivethreatenedspecies.appspot.com')
#The API Class
class SpeciesApi(remote.Service):
  
  #Search the bus stops from the query
  @endpoints.method(SearchCountriesRequest, SearchCountriesResponse, name='search.countries', path='search/countries', http_method='GET')
  def search_countries(self, request):
    
    country_list = get_country_list()
    query = request.q
    #Return an empty result for an empty query
    if query == "" or query == None:
        return SearchCountriesResponse(countries=country_list)
    
    
    matching = {}
    for country in country_list:
        ind = country.lower().find(query.lower())
        if ind != -1:
            matching[country] = ind
    
    #Sort the results by index
    matching_sorted = sorted(matching.iteritems(), key=lambda (k,v): (v,k))
    results = [country[0] for country in matching_sorted]
    
    return SearchCountriesResponse(countries=results)
  
  #Find the country code given a country
  @endpoints.method(CountryCodeRequest, CountryCodeResponse, name='search.code', path='search/code', http_method='GET')
  def country_to_code(self, request):
    
    code_list = get_code_list()
    
    query = request.q
    #Return an empty result for an empty query
    if query == "" or query == None:
        return CountryCodeResponse(code="")
    
    
    matching = {}
    for code in code_list:
        ind = country.lower().find(query.lower())
        if ind != -1:
            matching[country] = ind
    
    #Sort the results by index
    matching_sorted = sorted(matching.iteritems(), key=lambda (k,v): (v,k))
    results = [country[0] for country in matching_sorted]
    
    return SearchCountriesResponse(countries=results)
  
  
#Create the service
speciesapi_service = endpoints.api_server([SpeciesApi], restricted=False)