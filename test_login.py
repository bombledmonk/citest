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

#


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
        print(os.path.join(path, name), 'does not exist, error')
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
    res = search('p646-ND', tokenjson['access_token'])
    part = find_part_in_results(res, 'P646-ND')
    print(part)
    if part != False:
        return True
    else:
        return False



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
    # print(req.json())
    print(keyword, ' found')
    return req.json()


def find_part_in_results(results, searched_part):
    try:
        for part in results["Parts"]:
            if part.get("DigiKeyPartNumber") == searched_part:
                return part
        else:
            log_failed_pns(searched_part, results)
            return False
    except Exception as e:
        print(e)
        log_failed_pns(search)
        return False


def log_failed_pns (searched_part):
    print('failed to find ',searched_part, ' in results')

## check if token exists
## check if token works
## refresh token, then rewrite
## save into pn.json, add date, status
##

def get_data(cache_folder, pnlist, refresh=False):
    ## figure out how to timestamp data and only refresh if otherwise out of date
    ## try to figure out how to maintain travis cache
    if os.environ.get("CI") == 'true':
        print ('library builder on travis')
    else:
        print('local build')
        for i, pn in enumerate(pnlist):
            print(pn)
        ##TODO START HERE!!!!!!!!!!!



if __name__ == "__main__":
    token = load_access_token(CACHE_DIR,AUTH_TOKEN_FILENAME)
    print()
    if( token != False ):
        check_current_token(token)
    else:
        full_login_flow()
        
    get_data('',['300-8254-6-ND', 'FNETHE025DKR-ND'] )
    # assert False

##TODO
## make a file that stores something in cache
## access something in cache
## make test
