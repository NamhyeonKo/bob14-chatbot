import requests
import json

API_KEY = 'YOUR_VIRUSTOTAL_API_KEY'
domain = 'yotube.com'  # 분석할 도메인

url = 'https://www.virustotal.com/vtapi/v2/domain/report'
params = {'apikey': API_KEY, 'domain': domain}
response = requests.get(url, params=params)

print(response.status_code)
data = response.json()
print(json.dumps(data, indent=2))

# Hybrid Analysis API를 사용하여 도메인 분석 결과 조회

HYBRID_API_KEY = ''
headers = {
    'api-key': HYBRID_API_KEY,
    'accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded'
}
search_url = 'https://www.hybrid-analysis.com/api/v2/search/terms'
data = {'domain': domain}
resp = requests.post(search_url, headers=headers, data=data)

print(resp.status_code)
if resp.status_code == 200:
    print(json.dumps(resp.json(), indent=2))
else:
    print(resp.text)

# urlscan.io API를 사용하여 도메인 분석 결과 조회

URLSCAN_API_KEY = 'YOUR_URLSCAN_API_KEY'
urlscan_headers = {
    'API-Key': URLSCAN_API_KEY,
    'Content-Type': 'application/json'
}
urlscan_search_url = 'https://urlscan.io/api/v1/search/'
urlscan_params = {'q': f'domain:{domain}'}
urlscan_resp = requests.get(urlscan_search_url, headers=urlscan_headers, params=urlscan_params)

print(urlscan_resp.status_code)
if urlscan_resp.status_code == 200:
    print(json.dumps(urlscan_resp.json(), indent=2))
else:
    print(urlscan_resp.text)
