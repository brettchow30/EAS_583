import requests
import json

def pin_to_ipfs(data):
  assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
  #YOUR CODE HERE
  url = 'https://api.pinata.cloud/pinning/pinJSONToIPFS'
  headers = {   
    'Content-Type': 'application/json',   
    'pinata_api_key': "bf73394fecc48fe7b795",
    'pinata_secret_api_key': "c731b03ddc64ab1507211712e94d4123970d6ced8b41d13aaef0c5099de794b4"     
  }
  response_payload = {'pinataContent': data}

  response = requests.post(url=url, json=response_payload, headers=headers)
  if response.status_code == 200:
    cid = response.json()['IpfsHash']
  else:
    raise Exception("Failed to get CID")

  return cid

def get_from_ipfs(cid,content_type="json"):
  assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
  #YOUR CODE HERE	
  url = 'https://gateway.pinata.cloud/ipfs/'+str(cid)
  response = requests.get(url)
  if response.status_code == 200:
    data = json.loads(response.text)
  else:
    raise Exception("Failed to get data")
  assert isinstance(data,dict), f"get_from_ipfs should return a dict"
  return data
