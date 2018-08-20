import pytest

import pprint, requests, bs4, os, json
from requests import RequestException


REDIRECT = 'https://localhost/'
BASE_URL = 'https://sso.digikey.com'
SSO_URL = 'https://sso.digikey.com/as/authorization.oauth2'
TOKEN_URL = 'https://sso.digikey.com/as/token.oauth2'
SEARCH_URL = 'https://api.digikey.com/services/partsearch/v2/keywordsearch'
CACHE_DIR = '.cachedata'
AUTH_TOKEN_FILENAME = 'authtoken.json'

#Using envs for continuous integration
CLIENT_ID = os.environ['CLIENT_ID']
USERNAME = os.environ['USER_NAME']
PASSWORD = os.environ['PASSWORD']
CLIENT_SECRET = os.environ['CLIENT_SECRET']



def full_login_flow():
    login_page = f'{SSO_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT}'

    my_session = requests.Session()
    r = my_session.get(
        login_page
    )  #goes to login page to get the uniquely generated nonce form action

    soup = bs4.BeautifulSoup(r.text, features="html5lib")  #
    form_action = soup.select_one('form[action$=ping]')[
        'action']  #grabs only the form's action attribute
    form_login = BASE_URL + form_action

    login_data = {
        'pf.username': USERNAME,
        'pf.pass': PASSWORD,
        'pf.ok': 'clicked',
        'pf.cancel': ''
    }
    login_attempt = my_session.post(form_login, data=login_data, allow_redirects=False)

    print(login_attempt.status_code)
    auth_code = login_attempt.headers["Location"].split('=')[1]
    # with open('.cachedata/cachetest.txt', 'r') as out:
    #     print(out.readline())
    # with open('.cachedata/cachetest.txt', 'w') as out:
    #     out.write(auth_code)
    #     print('new auth_code', auth_code)
    auth_payload = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT
    }
    # load_access_token('.cachedata','authtoken.json')
    get_auth_token(my_session, TOKEN_URL, auth_payload)


def load_access_token(path,name):
    try:
        with open(os.path.join(path,name), 'r') as access_file:
            return json.load(access_file)
    except (FileNotFoundError, IOError):
        print(os.path.join(path, name), 'does not exist')
        return False


def get_auth_token(session, TOKEN_URL, auth_payload):
    session.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
    auth_result = session.post(TOKEN_URL, data=auth_payload)
    print (auth_result.status_code, auth_result.text )
    save_access_token('.cachedata','authtoken.json', auth_result)

def save_access_token(path, name, tokens):
    save_spot = os.path.join(path, name)
    with open(save_spot, 'w') as access_file:
        print('saving tokens')
        json.dump(tokens.json(), access_file)
    print('saving tokens ', path, name, tokens.json()['access_token'])


def check_current_token(tokenjson):

    search('342', tokenjson['access_token'])


def search(keyword, access_token, record_count=2):
    search_headers = {
        'accept': '*/*',
        'x-ibm-client-id': CLIENT_ID,
        'content-type': "application/json",
        'authorization': access_token
    }
    session = requests.Session()
    search_payload = {"Keywords": keyword, "RecordCount":record_count}
    for attempt in range(0,5):
        try:
            req = session.post(SEARCH_URL, headers=search_headers, json=search_payload, timeout=20)
            if (req.json().get('Results') == None):
                print ('Error for ', keyword, ' attempt ',attempt)
                continue
            elif ( req.json().get('Results')== 0):
                print('no results found for ', keyword, 'part may have been changed or removed from Digi-Key')
            break
        except RequestException as e:
            print ('RequestException',e)
            continue
        else:
            break
    else:
        print('failed all attempts for ', keyword)
    print(req.json())

## check if token exists
## check if token works
## refresh token, then rewrite
## save into pn.json, add date, status
##


if __name__ == "__main__":
    token = load_access_token(CACHE_DIR,AUTH_TOKEN_FILENAME)
    print()
    if( token != False ):
        check_current_token(token)
    else:
        full_login_flow()
    # assert False

##TODO
## make a file that stores something in cache
## access something in cache
## make test
