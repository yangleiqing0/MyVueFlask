import requests

session = requests.session()

url = 'http://188.131.183.182:2132/hahu/login'
params = {'email': '496520371@qq.com', 'password': '123456'}
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
content = session.post(url, params, headers=headers)
print(dict(session.cookies))

ask_url = 'http://188.131.183.182:2132/hahu/ask'
ask_params = {'params': '{"questionTitle":"213","questionContent":"<p>123</p>","topicKvList":"123"}'}
a = dict(session.cookies)
session = requests.session()
session.cookies = requests.utils.cookiejar_from_dict(a)
print('session.cookies', session.cookies.__dict__)
ask_content = session.post(ask_url, ask_params, headers=headers)
print(ask_content.status_code, ask_content.cookies, ask_content.text)
C = '{}'.format(session)

import requests

A = requests.session()

cc = eval('session')
print(cc.cookies, session, session.cookies._cookies)