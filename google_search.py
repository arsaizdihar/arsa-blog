import requests
import os

url = "https://google-search3.p.rapidapi.com/api/v1/search/q="

headers = {
    'x-rapidapi-key': os.environ.get("RAPID_API_KEY"),
    'x-rapidapi-host': "google-search3.p.rapidapi.com"
    }


def search_google(query):
    search_url = url + query
    response = requests.get(search_url, headers=headers)
    return response.json()["results"]
