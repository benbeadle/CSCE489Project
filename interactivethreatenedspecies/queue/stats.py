#!/usr/bin/env python

import webapp2, logging, json, csv, speciesapimessages, re, ndbpickler, unicodedata, models, queries, time
from google.appengine.api import memcache, rdbms
from google.appengine.ext import ndb
from collections import defaultdict, Counter

resp = None
params = {}

#Source: http://stackoverflow.com/questions/752308/split-array-into-smaller-arrays
def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
             for i in range(wanted_parts) ]

def run_stats():
    memcache.set("task|" + params["task_id"], {"status":"working"}, 3600)
    
    f = open("species.json")
    species = json.loads(f.read())
    f.close()
    #logging.info("Completed with {0} species".format(len(species)))
    
    query_lower = params["q"].lower()
    #Stands for header index
    def hi(s):
        res = [index for index,h in enumerate(headers) if h.lower()==s.lower()]
        if len(res) == 0:
            return -2
        return res[0]
    
    def weight(rls):
        if rls == "LC" or rls == "LR/cd" or rls == "LR/lc":
            return 1
        elif rls == "NT" or rls == "LR/nt":
            return 2
        elif rls == "VU":
            return 3
        elif rls == "EN":
            return 4
        elif rls == "CR":
            return 5
        elif rls == "EW":
            return 6
        elif rls == "EX":
            return 7
        return 0
    
    specie_count = 0
    counts = Counter()
    native_countries = Counter()
    for spec in species:
        spec_weight = weight(species[spec]["red_list"])
        if spec_weight == 0:
            continue
        names = " ".join([n[1] for n in species[spec]["names"]])
        if query_lower is not "" and names.lower().find(query_lower) is -1:
            continue
        specie_count += 1
        for country in species[spec]["countries"]:
            if country[0] == "Native":
                native_countries[country[1]] += 1
            counts[country[1]] += spec_weight
    logging.info("Most common for " + params["q"] + ": ")
    logging.info(counts.most_common(15))
    
    
    memcache.set("task|" + params["task_id"], {"status":"completed","countries":counts,"specie_count":specie_count,"native":native_countries}, 3600)
    
    
    return
    hic = hi("countries")
    hir = hi("Red List Status")
    while len(rows) > 0:
        row = rows.pop(0)
        
        countries = json.loads(row[hic])
        rls = row[hir]
        rls_weight = weight(rls)
        #If it's 0, then it's not one of the valid statuses (AKA DD - data deficient)
        if rls_weight == 0:
            continue
        for type in countries:
            for country in countries[type]:
                counts[country] += rls_weight
    print counts.most_common(10)
    
    memcache.set("task|" + params["task_id"], {"status":"completed"}, 3600)
    
    return
    
    """
    conn = rdbms.connect(instance='benbeadle-interactivespecies:interactivespecies', database='its')
    cursor = conn.cursor()
    
    begin = time.time()
    cursor.execute(queries.SPECIES_SEARCH.format("lizard"))
    ids_arr = [str(row[0]) for row in cursor.fetchall()]
    ids_arr = split_list(ids_arr, round(len(ids_arr) / 25))
    country_count = Counter()
    logging.info((time.time()) - begin)
    
    for ids in ids_arr:
        cursor.execute(queries.COUNTRY_STATS.format("','".join(ids)))
        logging.info((time.time()) - begin)
        logging.info(cursor.rowcount)
    logging.info("Done")
    """
    memcache.set("task|" + params["task_id"], {"status":"complete","count":cursor.rowcount}, 3600)
    return cursor.rowcount
    #for row in cursor.fetchall():
    #    id = row[0]
    #    
    #    return
    #return cursor.rowcount
    
class QueueHandler(webapp2.RequestHandler):
    def post(self):
        global resp, params
        resp = self.response
        #Save all of the parameters in a dictionary
        for myarg in self.request.arguments():
            params[myarg.encode('ascii')] = self.request.get(myarg).encode('ascii')
        res = run_stats()
        resp.headers['Content-Type'] = 'application/json'
        resp.write(json.dumps(res))
    def get(self):
        global resp, params
        resp = self.response
        #Save all of the parameters in a dictionary
        for myarg in self.request.arguments():
            params[myarg.encode('ascii')] = self.request.get(myarg).encode('ascii')
        res = run_stats()
        resp.headers['Content-Type'] = 'application/json'
        resp.write(json.dumps(res))
    
app = webapp2.WSGIApplication([
    ('/queue/stats', QueueHandler)
], debug=True)
