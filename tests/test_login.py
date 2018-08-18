import pytest

import pprint, requests, bs4, os

def test_login():
    mysession = requests.Session()
    redirect = 'https://localhost/'
    baseurl = 'https://sso.digikey.com'
    ssourl = 'https://sso.digikey.com/as/authorization.oauth2'

    client_id = os.environ['CLIENT_ID']
    username = os.environ['USER_NAME']
    password = os.environ['PASSWORD']
    loginPage = f'{ssourl}?response_type=code&client_id={client_id}&redirect_uri={redirect}'

    r = mysession.post(
        loginPage
    )  #goes to login page to get the uniquely generated nonce form action

    soup = bs4.BeautifulSoup(r.text, features="html5lib")  #
    formaction = soup.select_one('form[action$=ping]')[
        'action']  #grabs only the form's action attribute
    formlogin = baseurl + formaction

    loginData = {
        'pf.username': username,
        'pf.pass': password,
        'pf.ok': 'clicked',
        'pf.cancel': ''
    }
    loginAttempt = mysession.post(formlogin, data=loginData, allow_redirects=False)

    print(loginAttempt.status_code)
    code = loginAttempt.headers["Location"].split('=')[1]
    with open('.cachedata/cachetest.txt','r') as out:
        print(out.readline)
    with open('.cachedata/cachetest.txt','w') as out:
        out.write(code)
        print('new code',code)

if __name__ == "__main__":
    test_login()

##TODO
## make a file that stores something in cache
## access something in cache
## make test 