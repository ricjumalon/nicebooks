import json
from pip._vendor import requests

isbn = '1632168146'
res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "zGsh7G5dOXmEP6NOfvGGA", "isbns": isbn}).json()
#print(res.json())

data = json.dumps(res)
data = json.loads(data)
print(data['books'][0]['id'])
#data = json.loads(data)

#for item in data:
#    print(f"{item['isbn']}, ")