"""

Description: Contains methods for pickling and storing into memcache

Methods:
    route_info: Downloads the route info on the main transit page. The data is saved in an element on the page in the JSON format
    same_pattern_point: Returns if the two point parameters are the same location (lat and lng are the same)
"""
import pickle, logging
from google.appengine.api import memcache

def set(key, value, chunksize=950000):
  serialized = pickle.dumps(value, 2)
  values = {}
  for i in xrange(0, len(serialized), chunksize):
    values['%s.%s' % (key, i//chunksize)] = serialized[i : i+chunksize]
  memcache.set_multi(values)

def get(key):
  result = memcache.get_multi(['%s.%s' % (key, i) for i in xrange(32)])
  serialized = ''.join([v for k, v in sorted(result.items()) if v is not None])
  if serialized == "":
    return None
  return pickle.loads(serialized)