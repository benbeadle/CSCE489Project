"""
These are the Request and Response classes used by the Endpoints API to say what data is needed when calling API methods and what get's returned
"""
from protorpc import messages

class SearchCountriesRequest(messages.Message):
  q = messages.StringField(1)

class SearchCountriesResponse(messages.Message):
  countries = messages.StringField(1, repeated=True)

class CountryCodeRequest(messages.Message):
  country = messages.StringField(1)

class CountryCodeResponse(messages.Message):
  code = messages.StringField(1, required=True)
  possibilities = messages.StringField(2, repeated=True)