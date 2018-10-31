import pytest

import pprint, requests, bs4, os, json, argparse, time
from requests import RequestException
import shutil
from partkeys import InfoKeys
from generate_files import *
from libcheck import *
from filehelpers import *
from pathlib import Path



REDIRECT = 'https://localhost/'
BASE_URL = 'https://sso.digikey.com'
SSO_URL = 'https://sso.digikey.com/as/authorization.oauth2'
TOKEN_URL = 'https://sso.digikey.com/as/token.oauth2'
SEARCH_URL = 'https://api.digikey.com/services/partsearch/v2/keywordsearch'
CACHE_DIR = '.cachedata'
AUTH_TOKEN_FILENAME = 'authtoken.json'
DIGIKEY_DATA_CACHE = CACHE_DIR + '/digikeydata'

#Using envs for continuous integration
CLIENT_ID = os.environ['CLIENT_ID']
USERNAME = os.environ['USER_NAME']
PASSWORD = os.environ['PASSWORD']
CLIENT_SECRET = os.environ['CLIENT_SECRET']

SOURCE_SYMBOLS = '.cachedata/digikey-kicad-library/src/Source_Symbols'
SOURCE_FOOTPRINTS = '.cachedata/digikey-kicad-library/src/Source_Symbols'
RELEASE_SYMBOLS = '.cachedata/digikey-kicad-library/digikey-footprints.pretty'
RELEASE_FOOTPRINTS = '.cachedata/digikey-kicad-library/digikey-symbols'
REFERENCE_DESIGNATORS = 'familylist_refdes.csv'



def full_login_flow():
    print('starting full login')
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

    print('login status code ', login_attempt.status_code)
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
    print('done with full login')


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
    print('checking tokens')
    res = search('p646-ND', tokenjson['access_token'])
    # print('res is', res)
    part = find_part_in_results(res, 'P646-ND')
    # print('done checking part ', part)
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
                # print(req.json())
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
    # print(keyword, ' found')
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
##  add last updated field to cache



def get_website_data():
    pass

def get_kicad_filelist(infolder):
    ret = []
    nothandled = []
    totalfilecount = 0
    try:
        for file in os.listdir(infolder):
            totalfilecount += 1
            filename = os.fsdecode(file)
            if filename.endswith(".kicad_mod") or filename.endswith(
                    ".dcm") or filename.endswith(".lib"):
                ret.append(os.path.join(infolder, filename))
            else:
                nothandled.append(filename)
        print('found ', len(ret), ' out of ', totalfilecount,
              ' total files in ', infolder)
        if len(nothandled) > 0:
            print('\nthese files not handled \n', nothandled)
        return ret
    except Exception as e:
        print(e)


def get_info_from_masterlist_shim(symdata):
    '''This adds some extra information that used to come from a spreadsheet, but is no longer needed TODO refactor out'''
    symdatareturn = {p: {} for p in symdata}
    for part in symdata:
        # symdatareturn[part]
        symdatareturn[part]['Report Part Nbr'] = part
        symdatareturn[part]['Base Part Nbr'] = ''
        symdatareturn[part]['Include'] = "Yes"
        symdatareturn[part]['Footprint Completed By'] = "src"
        symdatareturn[part]['Symbol Completed By'] = "src"
    return symdatareturn

def get_info_from_source_symbols(symboldata):
    return [pn for pn in symboldata.keys()]

def get_authorization():
    token = load_access_token(CACHE_DIR, AUTH_TOKEN_FILENAME)
    if (token != False):
        print('token', token)
        if (check_current_token(token) == False):
            full_login_flow()
    else:
        full_login_flow()
    return load_access_token(CACHE_DIR, AUTH_TOKEN_FILENAME)  ## fix this silliness


def get_single_part_dict(part):
    mydict = {}
    try:
        mydict[part["DigiKeyPartNumber"]] = part
    except Exception as e:
        print('failure to parse Results', e, part)
    return mydict


def save_json(data, filepath):
    with open(filepath, 'w') as outfile:
        json.dump(data, outfile)


def load_json(filepath):
    try:
        with open(filepath, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(e)

def combine_dicts(dictlist):
    ## the first dict should be the most inclusive list
    ## following dicts are assumed subsets of the first list
    pns = sorted(dictlist[0].keys())  #base final list on pns in first dict
    outdict = {x: {} for x in dictlist[0].keys()}
    for d in dictlist:
        for pn in pns:
            #if key exists in supplimentary dicts, combine from two dicts into one parent
            if d.get(pn) != None:
                outdict[pn] = {**outdict[pn], **d[pn]}
    return outdict

def parts_to_build(d):
    """Returns a dictionary of only items where Include column was set to Yes in the management document"""
    # yes = {part: d[part] for part in d if d[part].get('Include') == "Yes"}
    withdata = {part: d[part] for part in d if d[part].get('Family') != None}
    return withdata

def add_buildpn(d, namesource):
    ##todo this needs some help and more error checking.
    ok = OutputKeys()
    taken = []
    failed = []
    for part in d:
        try:
            status = STATUS_MAP[find_param(d[part], 1989)[2]]
            if d[part].get('NonStock') == True and find_param(d[part],
                                                              1989)[2] == "0":
                status += "_NonStock"
            if d[part].get(namesource) not in taken:
                d[part]["buildpn"] = scrub_pn(d[part][namesource]) + status
                taken.append(d[part]["buildpn"])
            else:
                d[part]["buildpn"] = scrub_pn(
                    d[part][namesource] + d[part][ok.manname]['Id']) + status
                taken.append(d[part]["buildpn"])
        except Exception as e:
            # print('add_buildpn exception for part', part, e)
            print('buildpn fail test', e)
            failed.append(part)
            d[part]["Include"] = "API data not found"
    if failed:
        print("add_buildpn failed on", failed)
    return d

def get_data(cache_folder, symbol_data, token):
    ## figure out how to timestamp data and only refresh if otherwise out of date
    ## try to figure out how to maintain travis cache
    current_cache = load_json(cache_folder+'/website_data.json')
    if Path('/website_data.json').exists():
        if current_cache[pn].get('lastupdated') != None:
            pass

    return_val = {}
    token = load_access_token(CACHE_DIR, AUTH_TOKEN_FILENAME)
    pnlist = [pn for pn in symbol_data.keys()]

    ## load cache file,  check cache file for part number, check last updated, make request for that part.
    for i, pn in enumerate(pnlist):
 
        search_results = search(pn, token['access_token'], record_count=2)
        part = find_part_in_results(search_results, pn)
        single_part_dict = get_single_part_dict(part)
        return_val = {**return_val, **single_part_dict}
        if i>2:
            break
    save_json(return_val, cache_folder+'/website_data.json')
    return return_val




    # if os.environ.get("CI") == 'true':
    #     print('library builder on travis')
    #     for i, pn in enumerate(pnlist):
    #         pass
    #         # print(pn)
    #     # print(get_kicad_filelist(cache_folder+'/digikey-kicad-library/src/Source_Symbols'))

    # else:
    #     print('local build')
    #     for i, pn in enumerate(pnlist):
    #         # print(pn)
    #         pass
    # print('ok')
    ##TODO START HERE!!!!!!!!!!!



if __name__ == "__main__":
    print('main function')
    token = get_authorization()
    k = InfoKeys()

    symbol_file_list = get_kicad_filelist(SOURCE_SYMBOLS)
    # print(symbol_file_list)
    symbol_data = load_libraries(symbol_file_list)

    master_info = get_info_from_masterlist_shim(symbol_data)
    # pnlist = get_info_from_source_symbols(symbol_data)
    # includecount = 0
    # notincludecount = 0
    # for item in master_info:
    #     if master_info[item]['Include'] == 'Yes':
    #         includecount += 1
    #     else:
    #         notincludecount += 1
    # print('include count', includecount)



    website_data = get_data(CACHE_DIR, symbol_data, token)
    all_info = combine_dicts([master_info, website_data, symbol_data])
    all_info = parts_to_build(all_info)
    all_info = add_buildpn(all_info, k.mpn)
    check_metadata(all_info)
    generate_monlith(all_info, CACHE_DIR+'/monolith/', 'digikeyallparts', REFERENCE_DESIGNATORS)
    generate_by_families(all_info, CACHE_DIR+'/test/', REFERENCE_DESIGNATORS)



    # assert False
    print('main finished')

##TODO
## make a file that stores something in cache
## access something in cache
## make test
