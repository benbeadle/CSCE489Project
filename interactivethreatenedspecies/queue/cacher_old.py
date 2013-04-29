#!/usr/bin/env python

import webapp2, logging, json, csv, speciesapimessages, re, ndbpickler, unicodedata, models
from google.appengine.api import memcache,files
from google.appengine.ext import ndb
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

index = 0
def run_cacher():
    return
    logging.info("Done")
    input = ""
    count = 1
    with files.open("/gs/its/species.json", 'r') as f:
        data = f.read(5242880)
        while data:
            count += 1
            input += data
            data = f.read(5242880)
    logging.info("Done: " + str(len(json.loads(input))))
    logging.info("Count: " + str(count))
    
    return
    memcache.set("queue_cache", "running", time=60)
    logging.info("run_cacher")
    
    """
    f = open("animal_list.json")
    animal_list = json.loads(f.read())
    f.close()
    for ran in animal_list:
        ndbpickler.set("animal_list_" + ran, animal_list[ran])
    ndbpickler.stats()
    """
    
    """
    f = open("country_list.json")
    country_list = json.loads(f.read())
    f.close()
    cl = {}
    for item in country_list:
        cl[item["code"]] = item["name"]
    ndbpickler.set("country_list", cl)
    ndbpickler.stats()
    """
    logging.info("opening")
    f = open("species_" + str(index) + ".json")
    species = json.loads(f.read())
    logging.info("Read: " + str(len(species)))
    f.close()
    for i,s in enumerate(species):
        ndb_key = ndb.Key(models.Species, s["id"])
        m = models.Species(key=ndb_key)
        m.id=s["id"]
        m.major_threats=s["major_threats"]
        m.names=s["names"]
        m.countries=s["countries"]
        m.red_list_status=s["red_list"]
        m.population=s["population"]
        m.systems=s["systems"]
        m.habitat_ecology=s["habitat_ecology"]
        m.put()
        if i % 100 == 0:
            logging.info("Index: " + str(i))
     
    logging.info("Done!! Saved {0} species. There are {1} objs.".format(len(species), models.Species.query().count()))
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
    
    animal_list = {}
    for type in names:
        for name in names[type]:
            if name == "":
                continue
            if isinstance(name, str):
                animal_list[type].append(unicodedata.normalize('NFKD', unicode(name,errors="ignore")).decode('ascii', 'ignore'))
            else:
                animal_list[type].append(unicodedata.normalize('NFKD', name).encode('ascii', errors='ignore'))
    
    
    memcachepickler.set("animal_list", animal_list)
    
    
    
    memcache.delete("queue_cache")
    logging.info("run_cacher completed")


class QueueHandler(webapp2.RequestHandler):
    def post(self):
        global index
        index = self.request.get("index")
        run_cacher()
    def get(self):
        run_cacher()
    
app = webapp2.WSGIApplication([
    ('/queue/cacher', QueueHandler)
], debug=True)
