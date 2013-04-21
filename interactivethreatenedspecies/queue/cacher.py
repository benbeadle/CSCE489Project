#!/usr/bin/env python

import webapp2, logging, json, csv, speciesapimessages, re, memcachepickler, unicodedata
from google.appengine.api import memcache
from collections import defaultdict

resp = None
params = {}

def data_get_contents():
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

def iso_get_contents():
    rows = memcachepickler.get("file_ISOtoCountry")
    if rows != None:
        return rows
    f = open("ISOtoCountry.xls")
    reader = csv.reader(f)
    rows = [row for row in reader if row is not None]
    f.close()
    memcachepickler.set("file_ISOtoCountry", rows)
    return rows

def run_cacher():
    memcache.set("queue_cache", "running")
    logging.info("run_cacher")
    
    
    f = open("country_list.json")
    country_list = json.loads(f.read())
    f.close()
    memcache.set("country_list", country_list)
    del country_list
    
    
    animal_list = [{"name":"snake","type":"common"}, {"name":"bat","type":"common"}, {"name":"mouse","type":"common"}, {"name":"frog","type":"common"}, {"name":"rat","type":"common"}, {"name":"shrew","type":"common"}, {"name":"crayfish","type":"common"}, {"name":"lizard","type":"common"}, {"name":"warbler","type":"common"}, {"name":"wrasse","type":"common"}, {"name":"skink","type":"common"}, {"name":"gecko","type":"common"}, {"name":"snail","type":"common"}, {"name":"squirrel","type":"common"}, {"name":"salamander","type":"common"}, {"name":"shark","type":"common"}, {"name":"owl","type":"common"}, {"name":"finch","type":"common"}, {"name":"toad","type":"common"}, {"name":"turtle","type":"common"}, {"name":"dove","type":"common"}, {"name":"parrot","type":"common"}, {"name":"woodpecker","type":"common"}, {"name":"catfish","type":"common"}, {"name":"fish","type":"common"}, {"name":"monkey","type":"common"}, {"name":"lobster","type":"common"}, {"name":"toed","type":"common"}, {"name":"cuckoo","type":"common"}, {"name":"catshark","type":"common"}, {"name":"eel","type":"common"}, {"name":"sunbird","type":"common"}, {"name":"mole","type":"common"}, {"name":"parrotfish","type":"common"}, {"name":"honeyeater","type":"common"}, {"name":"viper","type":"common"}, {"name":"eagle","type":"common"}, {"name":"parakeet","type":"common"}, {"name":"worm","type":"common"}, {"name":"hawk","type":"common"}, {"name":"deer","type":"common"}, {"name":"opossum","type":"common"}, {"name":"antbird","type":"common"}, {"name":"gerbil","type":"common"}, {"name":"kingfisher","type":"common"}, {"name":"tiger","type":"common"}, {"name":"lemur","type":"common"}, {"name":"crab","type":"common"}, {"name":"hummingbird","type":"common"}, {"name":"angelfish","type":"common"}, {"name":"stingray","type":"common"}, {"name":"swallow","type":"common"}, {"name":"chameleon","type":"common"}, {"name":"cricket","type":"common"}, {"name":"duck","type":"common"}]
    memcache.set("animal_list", animal_list)
    """
    f = open("animal_list.json")
    animal_list = json.loads(f.read())
    f.close()
    memcachepickler.set("animal_list", animal_list)
    del animal_list
    """
    
    memcache.delete("queue_cache")
    logging.info("run_cacher completed")
    return
    
    #Import the data
    rows = data_get_contents()
    headers = rows.pop(0)
    
    #Stands for header index
    def hi(s):
        res = [index for index,h in enumerate(headers) if h.lower()==s.lower()]
        if len(res) == 0:
            return -2
        return res[0]
    
    #Loop through the rows and get the data
    country_index = hi("countries")
    
    kingdom_index = hi("kingdom")
    phylum_index = hi("phylum")
    class_index = hi("class")
    order_index = hi("order")
    family_index = hi("family")
    genus_index = hi("genus")
    species_index = hi("species")
    
    synonyms_index = hi("synonyms")
    common_name_index = hi("Common names (Eng)")
    scientific_name_index = hi("Scientific Name")
    
    country_list = set()
    
    names = {
        "kingdom": set(),
        "phylum": set(),
        "class": set(),
        "order": set(),
        "family": set(),
        "genus": set(),
        "species": set(),
        "synonym": set(),
        "common": set(),
        "Animal": set(),
        "scientific": set()
    }
    
    for row in rows:
        #Work on country data
        if row[country_index] == "N/A":
            continue
        countries = json.loads(row[country_index])
        for status in countries:
            #Some countries have their specific states. We don't care about that here
            country_list.update(set([country.split(" (")[0] for country in countries[status]]))
        
        names["kingdom"].add(row[kingdom_index].lower())
        names["phylum"].add(row[phylum_index].lower())
        names["class"].add(row[class_index].lower())
        names["order"].add(row[order_index].lower())
        names["family"].add(row[family_index].lower())
        names["genus"].add(row[genus_index].lower())
        names["species"].add(row[species_index].lower())
        names["scientific"].add(row[scientific_name_index].lower())
        names["synonym"].update(set(re.split(" *| *",row[synonyms_index].lower())))
        names["common"].update(set(re.split(",|-",row[common_name_index].lower())))
        
    country_list = list(country_list)
    
    iso_rows = iso_get_contents()
    
    code_dict = defaultdict(str)
    for row in iso_rows:
        #For countries that have commas, the row is split into more than just [country, code]
        if len(row) == 2:
            code_dict[row[0].lower()] = row[1]
        else:
            code = row.pop()
            code_dict[",".join(row).lower()] = code
    
    ret_list = [speciesapimessages.Country(name=country,code=code_dict[country.lower()]) for country in country_list]
    
    memcache.set("country_list", ret_list)
    
    animal_list = []
    for type in names:
        for name in names[type]:
            if name == "":
                continue
            if isinstance(name, str):
                animal_list.append({"name":unicodedata.normalize('NFKD', unicode(name,errors="ignore")).decode('ascii', 'ignore'),"type":type})
            else:
                animal_list.append({"name":unicodedata.normalize('NFKD', name).encode('ascii', errors='ignore'),"type":type})
    
    memcachepickler.set("animal_list", animal_list)
    
    memcache.delete("queue_cache")
    logging.info("run_cacher completed")


class QueueHandler(webapp2.RequestHandler):
    def post(self):
        run_cacher()
    def get(self):
        run_cacher()
    
app = webapp2.WSGIApplication([
    ('/queue/cacher', QueueHandler)
], debug=True)
