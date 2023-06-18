#!env/bin/python
import requests

cookies = {
    'SESSID': 'ABCDEF',
}

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Origin': 'https://www.example.com',
    'Accept-Encoding': 'gzip, deflate, br',
}

data = ''

response = requests.get('http://192.168.0.21/collect/all/series/movies/lang/hu', headers=headers, data=data)
if response.status_code == 200: 
    print(response.json())
else:
    print("Reason: {1}\nCode:   {0}".format(response.status_code, response.reason))