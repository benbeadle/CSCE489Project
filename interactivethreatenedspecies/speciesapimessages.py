"""
These are the Request and Response classes used by the Endpoints API to say what data is needed when calling API methods and what get's returned
"""
from protorpc import messages


class AnimalTypeEnum(messages.Enum):  
    KINGDOM = 1
    PHYLUM = 2
    CLASS = 3
    ORDER = 4
    FAMILY = 5
    GENUS = 6
    SPECIES = 7
    SCIENTIFIC = 8
    SYNONYM = 9
    COMMON = 10

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
  

class SearchDatabaseRequest(messages.Message):
  animal = messages.StringField(1, required=True)
  type = messages.EnumField(AnimalTypeEnum, 2, default='COMMON')
class SearchDatabaseResponse(messages.Message):
  countries = messages.MessageField(Country, 1, repeated=True)