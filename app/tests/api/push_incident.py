import datetime
import requests
import json


url = "http://127.0.0.1:5000/api/v1/incidents"
data = {
    "text": "Test incident API",
    "impact": "maintenance",
     "components": ["1,5"]
}
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

r = requests.post(url=url, data=json.dumps(data), headers=headers, timeout=2)

pastebin_url = r.text
print("The pastebin URL is:%s"%pastebin_url)

#my_list = [1,2,3,4,5]
#
#comps_string = "5,2,3"
#
#selected_components = list(map(int, comps_string.split(",")))
#
#print(selected_components)