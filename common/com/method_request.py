# encoding=utf-8
import requests
import time
from modles import Variables
from flask import session


class MethodRequest:

    def __init__(self):
        self.session = requests.session()
        if session.get('request_{}'.format(session.get('user_id'))):
            self.session = session['request_{}'.format(session.get('user_id'))]

    def request_value(self, method, url, data, headers):
        user_id = session.get('user_id')
        headers.update({'Connection': 'close'})
        print('请求方法: ', method, url, data, headers, type(url))
        new_data = ''
        for c in data:
            # 判断是否有中文  有的话进行解析
            if ord(c) > 255:
                c = c.encode('UTF-8').decode('latin1')
            new_data += c
        data = new_data
        requests.adapters.DEFAULT_RETRIES = 51
        requests.session().keep_alive = False
        timeout = Variables.query.filter(Variables.name == '_Request_Time_Out',
                                         Variables.user_id == user_id).first().value
        if timeout and timeout.isdigit():
            timeout = int(timeout)
        else:
            timeout = 5
        try:
            if method.upper() == 'GET':
                if 'https' in url:
                    print('True')
                    result = self.session.get(url, headers=headers, verify=False, timeout=timeout).text
                else:
                    result = self.session.get(url, headers=headers, timeout=timeout).text
            elif method.upper() == 'POST':
                if 'https' in url:
                    result = self.session.post(url, data=data, headers=headers, verify=False, timeout=timeout).text
                else:
                    result = self.session.post(url, data=data, headers=headers, timeout=timeout).text
            elif method.upper() == 'PUT':
                if 'https' in url:
                    result = self.session.put(url, data=data, headers=headers, verify=False, timeout=timeout).text
                else:
                    result = self.session.put(url, data=data, headers=headers, timeout=timeout).text
            elif method.upper() == 'DELETE':
                if 'https' in url:
                    result = self.session.delete(url, data=data, headers=headers, verify=False, timeout=timeout).text
                else:
                    result = self.session.delete(url, data=data, headers=headers, timeout=timeout).text
            else:
                result = "请求方法不正确"
        except Exception as e:
            print(e)
            time.sleep(0.5)
            result = "解析请求结果失败 : %s" % e
        session['request_{}'.format(session.get('user_id'))] = self.session
        return result
