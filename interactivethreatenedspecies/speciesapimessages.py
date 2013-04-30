"""
These are the Request and Response classes used by the Endpoints API to say what data is needed when calling API methods and what get's returned
"""
from protorpc import messages

class SearchCountriesRequest(messages.Message):
  q = messages.StringField(1)
class Country(messages.Message):
    name = messages.StringField(1, required=True)
    code = messages.StringField(2, required=True)
    rating = messages.IntegerField(3)
class SearchCountriesResponse(messages.Message):
  countries = messages.MessageField(Country, 1, repeated=True)

  
class SearchAnimalsRequest(messages.Message):
  q = messages.StringField(1)
class AnimalResult(messages.Message):
    name = messages.StringField(1)
    type = messages.StringField(2)
class SearchAnimalsResponse(messages.Message):
  animals = messages.MessageField(AnimalResult, 1, repeated=True)
  

class StatsInitRequest(messages.Message):
  q = messages.StringField(1, required=True)
class StatsInitResponse(messages.Message):
  task_id = messages.StringField(1, required=True)

class StatsStatusRequest(messages.Message):
  task_id = messages.StringField(1, required=True)
class StatsStatusResponse(messages.Message):
  status = messages.StringField(1, required=True)
  specie_count = messages.IntegerField(2)
  countries = messages.MessageField(Country, 3, repeated=True)
  common_countries = messages.MessageField(Country, 4, repeated=True)
  native_countries = messages.MessageField(Country, 5, repeated=True)