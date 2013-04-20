"""
These are the Request and Response classes used by the Endpoints API to say what data is needed when calling API methods and what get's returned
"""
from protorpc import messages

class SearchCountriesRequest(messages.Message):
  q = messages.StringField(1)

class Country(messages.Message):
    name = messages.StringField(1)
    code = messages.StringField(2)
class SearchCountriesResponse(messages.Message):
  countries = messages.MessageField(Country, 1, repeated=True)

  
class SearchAnimalsRequest(messages.Message):
  q = messages.StringField(1)
class AnimalResult(messages.Message):
    name = messages.StringField(1)
    type = messages.StringField(2)
class SearchAnimalsResponse(messages.Message):
  animals = messages.MessageField(AnimalResult, 1, repeated=True)
  

class PageLoadRequest(messages.Message):
  dummy_field = messages.StringField(1) #Dummy field
class PageLoadResponse(messages.Message):
  result = messages.BooleanField(1, default=True)