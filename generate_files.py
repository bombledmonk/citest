import os, re, pprint, time, json, csv
from pyparsing import ParseException
from schematicparser import libraryparser, docparser
from partkeys import InfoKeys, OutputKeys
from filehelpers import clean_folder

ATTRIBUTE_MAP = [
    ('Digi-Key_PN', "DigiKeyPartNumber"),
    ('MPN', "ManufacturerPartNumber"),
    ('Category', "Category", "Text"),
    ('Family', 'Family', "Text"),
    ('DK_Datasheet_Link', "PrimaryDatasheet"),
    ('DK_Detail_Page', "PartUrl"),
    ('Description', "ProductDescription"),
    ('Manufacturer', "ManufacturerName", "Text"),
    ('Status', "Parameters", "Text"),
]

STATUS_MAP = {
    '0':'', #active
    '2':'_Discontinued',
    "7":'_NRND',
    '4':'_LTB',
    '1':'_Obsolete',
    '3':'_Prelim'
}


def generate_monlith(d, outfolder, libname, refdesfile):
    os.makedirs(os.path.dirname(outfolder), exist_ok=True)
    clean_folder(outfolder)
    generate_lib(d, outfolder, libname, refdesfile)
    generate_dcm(d, outfolder, libname)
    check_symbol_libs(outfolder)
    print("generate_monlith done", len(d))


def generate_by_categories(d, outputfolder, refdesfile):
    bycat = split_into_cat_dicts(d)
    for key in bycat:
        generate_lib(bycat[key], outputfolder, sanitize_family_name(key), refdesfile)
        generate_dcm(bycat[key], outputfolder, sanitize_family_name(key))
    print('done generate_by_categories')
    return outputfolder


def generate_by_families(d, outputfolder, refdesfile):
    bycat = split_into_fam_dicts(d)
    for key in bycat.keys():
        generate_lib(bycat[key], outputfolder, sanitize_family_name('dk_' + key), refdesfile)
        generate_dcm(bycat[key], outputfolder, sanitize_family_name('dk_' + key))
    print('done generate_by_familes')
    return outputfolder


def load_libraries(liblist):
    fulldict = {}
    for lib in liblist:
        try:
            with open(lib, 'r') as f:
                filetext = f.read()
                parsedLibrary = libraryparser.parseString(
                    filetext, parseAll=True)
                libraryDict = parsedLibrary['parts']
                # print(parsedLibrary)
                # libraryDict.pprint()
                # z=(libraryDict.items())
                # for x in libraryDict:
                #     print('hi')
                #     z = x
                # print(x)
                # print(libraryDict)
                # partsDict = {part["partnumber"]: part for part in libraryDict}
                partsDict = {}
                for part in libraryDict:
                    # print(part)
                    footprint = ''
                    if ':' in part['fns']['F2'][1]:
                        footprint = part['fns']['F2'][1].replace('"','').split(
                            ':')[1]
                        # print(footprint)
                    else:
                        footprint = part['fns']['F2'][1].replace('"','')
                        # print('debugfp', footprint)
                    partsDict[part['partnumber']] = {
                        'def': part.get('def'),
                        'draw': part.get('draw'),
                        'fns': part['fns'],
                        'partnumber': part.get('partnumber'),
                        'sourcelib': os.path.basename(lib),
                        'sourcefp': part['fns']['F2'][1],
                        'Footprint Filename': footprint
                    }
                    if ':' not in part['fns']['F2'][1]:
                        print(partsDict[part['partnumber']]["Footprint Filename"], 'is missing digikey-footprints in symbol library assignment')

                for part in partsDict:
                    # partsDict[part]["sourcelib"] = os.path.basename(lib)
                    # partsDict[part]["sourcefp"] = partsDict[part]['fns']['F2'][1] #store the fp name from part
                    if len(partsDict[part]["sourcefp"]) <=5 :  # check the symbols for missing footprint assignments
                        print(part, 'is missing a footprint', partsDict[part]["sourcefp"])
                    # partsDict[part].pprint()
                    # print([x for x in partsDict[part].keys()])
                    # assert True, 'hi'STARTHERE AGAIN
                    if partsDict[part]["partnumber"] + '_FRAC' in libraryDict:
                        partsDict[part]["partnumber"]['frac'] = partsDict.get(
                            partsDict[part]["partnumber"] + '_FRAC')
                        print(partsDict[part]["partnumber"] + '_FRAC')
                # partsDict["sourcelib"] = lib
                fulldict = {**fulldict, **partsDict}
                # print(fulldict)
        except ParseException as pe:
            print("couldn't parse",lib, pe)
            # assert True, 'hi2'
    print(len(fulldict.keys()), 'parts loaded from',len(liblist),'libraries\n')
    return fulldict


def split_into_fam_dicts(allpartdata):
    #todo change to use defaultdict
    fams = {}
    for key in allpartdata.keys():
        i = allpartdata[key]["Family"]["Id"]
        t = allpartdata[key]["Family"]["Text"]
        if allpartdata[key]["Family"]["Text"] == "Accessories":
            t = allpartdata[key]["Category"]["Text"] + '_' + t

        if fams.get(t) == None:
            fams[t] = {}
            fams[t][key] = allpartdata[key]
        else:
            fams[t][key] = allpartdata[key]


#         print(fams.keys())
    return fams


def split_into_cat_dicts(allpartdata):
    cats = {}
    for key in allpartdata.keys():
        i = allpartdata[key]["Category"]["Id"]
        t = allpartdata[key]["Category"]["Text"]
        if cats.get(t) == None:
            cats[t] = {}
            cats[t][key] = allpartdata[key]
        else:
            cats[t][key] = allpartdata[key]
    return cats


def check_symbol_libs(infolder):
    ##todo add individual file check
    for file in os.listdir(infolder):
        check_symbol_lib(file, infolder)


def check_symbol_lib(file, infolder):
    if file.endswith(".dcm"):
        # print(file)
        try:
            with open(os.path.join(infolder, file), 'r') as f:
                x = f.read()
                l = docparser.parseString(x, parseAll=True)
                print('checking dcm', file, len(l['docparse']['partlist']),
                      'parts found')
        except ParseException as e:
            print("parse Exception on", file, e)
    elif file.endswith('.lib'):
        # print(file)
        try:
            with open(os.path.join(infolder, file), 'r') as f:
                x = f.read()
                l = libraryparser.parseString(x, parseAll=True)
                print('checking lib', file, len(l['parts']), 'parts found')
        except ParseException as e:
            print('------------------', e)


def build_lib_item(partdict, refdesfile , nodata=False):
    # nodata is for generating barebones symbols without DK data
    partnumber = partdict['DigiKeyPartNumber'].replace(' ', '')
    if nodata == False:
        partnumber = partdict['buildpn']
    attrx = str(200)
    #     partnumber = partdict['ManufacturerPartNumber'].replace(' ','')
    ##todo fix CNN spacing problem on f0-3
    ##todo make sure I can name parts with mfg or dkpn, need to edit def line and F1
    partlines = [
        '#',
        '# ' + partnumber,
        '#',
    ]
    fns = partdict.get('fns')
    # print(partnumber)
    if fns != None:
        mygen = get_vertical_pos(100)
        partdict['def'][1] = partnumber if "~" not in partdict['def'][
            1] else '~' + partnumber
        partlines.append(' '.join(partdict['def']))
        fns[0][1] = '"' + get_refdes(partdict,refdesfile) + '"'  #F0 refdes text
        fns[1][1] = '"' + partnumber + '"'  #F1 symbol name same as in defline
        footprint = partdict.get("Footprint Filename")
        #         print(footprint)
        if footprint == None:
            print(partnumber, 'has no footprint specified in source')
            footprint = "None"
        fns[2][1] = (
            '"digikey-footprints:' + footprint + '"')  #F2 footprint name
        fns[2][2] = attrx
        fns[2][3] = next(mygen)
        fns[2][7] = 'L'
        if nodata == True:
            fns[3][1] = '""'  #F3 datasheet
            fns[3][2] = attrx
            fns[3][3] = next(mygen)
            fns[3][7] = 'L'
            for fn in fns:
                partlines.append(' '.join(fn))
        else:
            fns[3][1] = '"' + partdict["PrimaryDatasheet"] + '"'  #F3 datasheet
            fns[3][2] = attrx
            fns[3][3] = next(mygen)
            fns[3][7] = 'L'

            for fn in fns:
                partlines.append(' '.join(fn))

            for idx, attr in enumerate(ATTRIBUTE_MAP, start=4):
                item = ""
                if isinstance(partdict[attr[1]], dict):
                    item = partdict[attr[1]]["Text"]
                    # print('Text####', item)
                elif attr[1] == "Parameters":
                    item = find_param(partdict, 1989)[1]
                    if partdict["NonStock"] == True:
                        item += ' NonStock'
                else:
                    item = partdict[attr[1]]
                    # print('else**************', attr[1],item)
                # print('fallout', partdict[attr[1]])
                partlines.append("F" + str(idx) + ' "' + (
                    item.replace('"', '')) + '" ' + attrx + ' ' + next(mygen) +
                                 ' 60 H I L CNN' + ' "' + attr[0] + '"')

        partlines.append('DRAW')
        partlines.append(partdict['draw'].strip())
        partlines.append('ENDDRAW')
        partlines.append('ENDDEF')
    else:
        print('missing library data for', partdict['DigiKeyPartNumber'])
    return partlines


def find_param(partdict, paramid):
    paramlist = partdict.get('Parameters')
    if paramlist is not None:
        for param in paramlist:
            # print(param.get("ParameterId") == paramid, param)
            if param.get("ParameterId") == paramid:
                return (param["Parameter"], param["Value"], param["ValueId"])
    else:
        print("parameter", paramid ,"not found in",)

    return (None, None, None)


def sanitize_family_name(name):
    return name.replace('/', '-').replace(' ', '-').replace(',', '').replace(
        '_-_', '-').replace('---','-').replace('(','').replace(')','')


def generate_dcm(d, outdir, filename):
    alldcm = ["EESchema-DOCLIB  Version 2.0"]
    for key in sorted(d.keys()):
        if d[key].get('Include') == 'Yes':
            alldcm.append('\n'.join(build_dcm_item(d[key])))
    alldcm.append('#End Doc Library')
    print()
    with open(os.path.join(outdir, filename + '.dcm'), 'w') as f:
        f.write('\n#\n'.join(alldcm))
    print('successfully wrote', filename, 'DCM')


def build_dcm_item(partdict, pntype=True):
    if (pntype == True):
        mainpn = partdict["DigiKeyPartNumber"].replace(' ', '')
        secondarypn = partdict["ManufacturerPartNumber"].replace(' ', '')
    else:
        mainpn = partdict["ManufacturerPartNumber"].replace(' ', '')
        secondarypn = partdict["DigiKeyPartNumber"].replace(' ', '')
    mainpn = partdict["buildpn"]
    secondarypn = partdict["DigiKeyPartNumber"].replace(' ', '')

    dcm = []
    dcm.append("$CMP " + mainpn)
    dcm.append('D ' + partdict["ProductDescription"])
    dcm.append('K ' + secondarypn + ' ' +
               (partdict["Series"]["Value"]
                if partdict["Series"]["Value"] != "-" else ""))
    dcm.append('F ' + partdict['PrimaryDatasheet'])
    dcm.append('$ENDCMP')
    return dcm


def generate_single_part_libs(d, outdir, refdesfile='./data/familylist_refdes.csv'):
    for key in d:
        generate_lib({key: d[key]}, outdir, sanitize_family_name(key), refdesfile, True)


def generate_lib(d, outdir, filename, refdesfile, nodata=False):
    #TODO think about adding generate date
    cnt = 0
    with open(os.path.join(outdir, filename + '.lib'), 'w', newline='') as of:
        of.writelines("\n".join(
            ["EESchema-LIBRARY Version 2.3", "#encoding utf-8"]))
        #         print(d.keys())
        for part in sorted(d.keys()):
            if d[part].get("Include") == 'Yes' or nodata == True:
                if d[part].get('fns') != None:
                    of.write('\n')
                    of.write('\n'.join(build_lib_item(d[part],refdesfile, nodata)))
            else:
                print(part, 'Include', d[part].get('Include'))
        of.write('\n#\n#End Library\n')
    print("successfully wrote ", filename, "lib")


def get_refdes(part, refdesfile="./data/familylist_refdes.csv"):
    if refdesfile.endswith('csv'):
        with open(refdesfile,'r') as f:
            c = csv.reader(f)
            refjson = {}
            for row in c:
                refjson[row[0]] = {'Id':row[0], 'Text':row[1], 'Refdes':row[2]}
    elif refdesfile.endswith('.json'):
        with open(refdesfile, 'r') as f:
            refjson = json.load(f)
    else:
        print('refdes fileread problems')
    famid = part["Family"]["Id"]
    if refjson.get(famid) != None:
        refdes = refjson[famid]["Refdes"]
        # print(refdes)
    else:
        refdes = "U?"
        print('No refdes assigned for ', part["Family"])
    return refdes


def scrub_pn(pntext):
    return re.sub(r'[^\w\d\_\-]', '_', pntext)


def get_vertical_pos(start):
    position = start
    step = 100
    while True:
        position = position + step
        yield str(position)
