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

print("Series:")
response = requests.get('http://192.168.0.21/collect/all/series/movies/lang/hu', headers=headers, data=data)
if response.status_code == 200: 
    for record in response.json():
        if record["title_req"]:
            orig_title = "(Original [{1}]: {0})".format(record["title_orig"], record["lang_orig"]) if record["title_orig"] else ""
            print("Id: {0}, Title: {1} {2}".format(record["id"], record["title_req"], orig_title))
        else:
            print("Id: {0}, Title: (Original [{1}]) {2}".format(record["id"], record["lang_orig"], record["title_orig"]))

        child_response = requests.get('http://192.168.0.21/collect/child_hierarchy_or_card/id/'+ str(record["id"]) + '/lang/hu', headers=headers, data=data)
        for child_record in child_response.json():
            if child_record["title_req"]:
                child_orig_title = "(Original: {0})".format(child_record["title_orig"]) if child_record["title_orig"] else ""
                print("       {1} {2}".format(child_record["id"], child_record["title_req"], child_orig_title))
            else:
                print("       (Original: {2}".format(child_record["id"], child_record["title_orig"]))
else:
    print("Reason: {1}\nCode:   {0}".format(response.status_code, response.reason))


print("Dramas:")
response = requests.get('http://192.168.0.21/collect/standalone/movies/genre/drama/lang/hu', headers=headers, data=data)
if response.status_code == 200: 
    for record in response.json():
        if record["title_req"]:
            orig_title = "(Original [{1}]: {0})".format(record["title_orig"], record["lang_orig"]) if record["title_orig"] else ""
            print("Id: {0}, Title: {1} {2}".format(record["id"], record["title_req"], orig_title))
        else:
            print("Id: {0}, Title: (Original [{1}]) {2}".format(record["id"], record["lang_orig"], record["title_orig"]))
else:
    print("Reason: {1}\nCode:   {0}".format(response.status_code, response.reason))
