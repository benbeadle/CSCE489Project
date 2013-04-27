"""

Description: Use NDB to store json objects. For dictionaries too big to save in one NDB Object (*cough* the graph *cough*),
this "pickles" the graph saving it in multiple NDBJsonPickler objects. It always saves with keys key|index, starting with 0.
The last saved NDBJsonPickler's "last" attribute is set to True. This way, if the same key was pickled before, and required
more NDBJsonPickler objects, it'll ignore the objects after it.

Using NDB as opposed to DB allows for automatic caching. (Why didn't I find out about this option earlier!?)

"""
import math, json, logging
import models
from google.appengine.ext import ndb
from collections import Counter

#Save the dictionary when it surpasses this size (using len(json.dumps))
#Note: Current implementation hypothetically could crash if the dict is a dict of dicts as it doesn't
#iterate through the dictionary's items.
NDB_CACHER_CHUNKSIZE = 500000.0
ndbpickler_stats = Counter()

#TODO: The chunksize above is not the maximum, but a stopping point when then length surpases that value

#Save the data using the Datastore
#This isn't iterative, so if a subdictionary is too big, this will fail
def set(key, input_dict):
    global ndbpickler_stats
    
    key_lower = key.lower()
    temp = {} #The temporary dictionary added to and then cleared once it's been saved
    index = 0
    last_obj = None #Save the last object to set it's last attribute to True
    
    #Loop through the dictionary
    for item in input_dict:
        #Add this item to the temp dict
        temp[item] = input_dict[item]
        
        #If temp is longer than the chunksize, save it go the datastore
        #Also reset the dict and increase the index
        if len(json.dumps(temp)) >= NDB_CACHER_CHUNKSIZE:
            ndb_key = ndb.Key(models.NDBJsonPickler, key+"|"+str(index))
            last_obj = models.NDBJsonPickler(key=ndb_key, type=key_lower, last=False, index=index, data=temp)
            last_obj.put()
            temp = {}
            index += 1
    
    #After looping through the dictionary, if there are some stragglers, go ahead and save those
    if len(json.dumps(temp)) > 0:
        ndb_key = ndb.Key(models.NDBJsonPickler, key+"|"+str(index))
        last_obj = models.NDBJsonPickler(key=ndb_key, type=key_lower, last=True, index=index, data=temp)
        last_obj.put()
    
    #Set the last saved object's last property to True
    if last_obj is not None:
        last_obj.last = True
        last_obj.put()
    
    ndbpickler_stats["set_called"] += 1
    ndbpickler_stats["set_objects_put"] += (index+1)
    
#Now aggregate the split datastore objects into one to return
def get(key):
    global ndbpickler_stats
    ndbpickler_stats["get_called"] += 1
    #Now get the results and make sure there are some
    results = models.NDBJsonPickler.query().order(models.NDBJsonPickler.index).filter(models.NDBJsonPickler.type == key.lower())
    if results.count() == 0:
        ndbpickler_stats["get_no_results"] += 1
        return None
    
    result = {}
    
    for json_obj in results:
        ndbpickler_stats["get_total_objects"] += 1
        result = dict(result.items() + json_obj.data.items())
        if json_obj.last == True:
            break
    return result

def stats():
    logging.info("ndbpickler stats: " + str(ndbpickler_stats))