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
    memcache.set("task|" + params["task_id"], {"status":"working"})
    
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
    memcache.set("task|" + params["task_id"], {"status":"complete","count":cursor.rowcount})
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
    
app = webapp2.WSGIApplication([
    ('/queue/stats', QueueHandler)
], debug=True)
