"""
This contains the models used in the Datastore

Version: 1.0
"""
from google.appengine.ext import ndb

class NDBJsonPickler(ndb.Model):
    index = ndb.IntegerProperty()
    last = ndb.BooleanProperty()
    type = ndb.StringProperty()
    data = ndb.PickleProperty()



class Species(ndb.Model):
    major_threats = ndb.TextProperty()
    id = ndb.StringProperty()
    red_list_status = ndb.StringProperty()
    names = ndb.StringProperty(repeated=True)
    population = ndb.TextProperty()
    countries = ndb.StringProperty(repeated=True)
    systems = ndb.StringProperty(repeated=True)
    habitat_ecology = ndb.TextProperty()