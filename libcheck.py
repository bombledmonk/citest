from collections import defaultdict
# import multiprocessing
from natsort import natsort_keygen, ns, natsorted
from partkeys import InfoKeys, OutputKeys
import os
import pprint
import sexpr

def get_symbol_pin_count(drawingtext):
    draw = drawingtext.split('\n')
    pincount = 0
    for line in draw:
        if line.startswith('X'):
            pincount +=1
    return pincount

def get_footprint_pad_count(fppath):
    fplib = "../Output/test1/testfplib.pretty"
    testpart1 = '8-DSBGA.kicad_mod'
    testpart2 = '16-VFQFN_Exposed_Pad(3x3).kicad_mod'
    testpart3 = '100-HTQFP-14x14.kicad_mod'
    keys = [key for key in allinfodict.keys()]
    # print(allinfodict[keys[0]])
    pdict = {}
    padcount = 0
    # print(fppath)
    with open(fppath, 'r') as f:
        for line in f:
            ls = line.strip()
            if ls.startswith('(pad'):
                padcount += 1
                lsplit = ls.split(' ')[1]
                # print (lsplit)
                pdict[lsplit] = 1
                # print(line.strip().split(' ')[1])

        # print(len(pdict.keys()), padcount, '\t',fppath)
    return (len(pdict.keys()), padcount, fppath)

def check_repeat_pins(d):
    conflicts = []
    for part in d:
        if 'draw' in d[part]:
            drawlist = get_drawing_list(d[part]["draw"])
            pins = get_pin_list(drawlist)
            # lines = d[part]["draw"].split('\n')
            found = {}
            for l in pins:
                linelist = l.split(' ')
                if linelist[2] not in found:
                    found[linelist[2]] = linelist[1:3]
                else:
                    conflicts.append((
                        d[part].get("DigiKeyPartNumber"),
                        'mult pins',
                        linelist[1],
                        linelist[2],
                        'conflicts with',
                        found[linelist[2]],
                        d[part].get('sourcelib')
                    ))
        else:
            print('nodrawdata', d[part].get("DigiKeyPartNumber"))
    return sorted(con, key=lambda x: x[6])


def get_pins(drawtext):
    drawlist = drawtext.split('\n')
    pins = [x for x in drawlist if x.startswith('X') ]
    return pins

def calculate_bounding_box(drawtext):
    pass

def get_drawing_list(drawtext):
    return drawtext.split('\n')

def get_pin_list(drawing_list):
    return [x for x in drawing_list if x.startswith('X') ]

def compare_symbol_footprint(d, fpdir, status=["Active"], release=["Yes"]):
    print('\ncomparing symbols and footprints')
    k = InfoKeys()
    keylist = []
    missing = defaultdict(lambda: [])
    schem2fp = defaultdict(lambda: [])
    keylist = [key for key in d if d[key].get("Include") in release]
    # keylist = d.keys()

    for partkey in keylist:
        part=d[partkey]
        if part.get(k.status) in status or status == "All":
            # if True:  #to include inactive parts
            pins = []
            pinnums = []
            padlist = []
            if ('draw' in part) and (part.get(k.fp) != None):
                drawlist = get_drawing_list(part['draw'])
                pins = get_pin_list(drawlist)
                pinnums = get_pin_nums(pins)
                padlist = get_pad_list(part.get(k.fp), fpdir, d)
                if padlist is not None:
                    for pad in padlist:
                        if ( pad not in [None, ""]) and (str(pad) not in pinnums):
                            i = [partkey,
                                  'sym missing pin for pad',
                                  str(pad),
                                  'in',
                                  part.get(k.fp),
                                  'fp:'+str(part.get(k.fpby)),
                                  's:'+str(part.get('sourcelib'))
                                ]
                            if(i not in missing[' '.join(i)]):
                                missing[' '.join(i)].append(i)
                    for pin in pinnums:
                        if(pin not in [None] and pin not in padlist):
                            i = [partkey,
                                'there is no pad for pin',
                                str(pin),
                                'in fp',
                                 part.get(k.fp),
                                'fp:'+str(part.get(k.fpby)),
                                's:'+str(part.get('sourcelib')),
                                 'pad:'+ ' '.join(natsorted(padlist)),
                                 'pin:'+ ' '.join(natsorted(pinnums))
                                ]
                            if partkey not in schem2fp[partkey]:
                                schem2fp[partkey]=i
            else:
                print(partkey,'nopins', 'status', part.get(k.status), )
    f = [missing[x] for x in missing.keys()]
    pprint.pprint( sorted(f, key=lambda f: f[0][6]), width=150)
    g = [schem2fp[x] for x in schem2fp.keys()]
    # pprint.pprint(schem2fp)
    print('-----------------------')
    # pprint.pprint( natsorted(g, key=lambda g: g[0][6]), width=150)
    pprint.pprint(g, width=250)
    print('done comparing symbols and footprints\n')


def get_pad_list(fpname,fpdir, d):
    try:
        with open(os.path.join(fpdir,fpname+'.kicad_mod'),'r') as f:
            text = f.read()
            fp_sexpr = sexpr.parse_sexp(text)
            out = [str(x[1]) for x in fp_sexpr if (type(x) == list and 'pad' in x[0])]
            # if (fpname == "Module_WIZ810MJ" ):
            #     pprint.pprint(fp_sexpr)
            return out
    except Exception as e:
        # x = get_symbols_with_footprint(d,fpname)
        # for i in x:
        # print(d[i].get())
        print(get_symbols_with_footprint(d,fpname),'no file named', fpname)
        print(e)
        # print(get_symbols_with_footprint(d,fpname),'problem with', fpname ,e) ##todo remove global
        return None


def get_pin_nums(pins):
    return [p.split(' ')[2] for p in pins]


def find_max_pad_num(padlist):
    # parse_sexp(sexp)
    pass


def check_footprints(d, libpath):
    k = InfoKeys()
    missing_files = []
    missing_draw = []
    missing_fpname = []
    non_active_parts = []
    for part in d:
        if d[part].get(k.status) != "Active":
            print(part, d[part].get(k.status))
            try:
                # print(d[part].get("Footprint Filename"))
                fpfilename = d[part].get("Footprint Filename")
                if 'draw' in d[part] and fpfilename != None:
                    fpcnt = get_footprint_pad_count(os.path.join(libpath, fpfilename+'.kicad_mod'))
                    scnt = get_symbol_pin_count(d[part].get('draw'))
                    # print(get_symbol_pin_count(d[part].get('draw')))
                    if scnt != fpcnt[0]:
                        # print(scnt, fpcnt, part, d[part].get("Footprint Completed By"), d[part].get("Symbol Completed By"))
                        pass
                elif('draw' not in d[part]):
                    missing_draw.append((part, ' has no draw'))
                elif fpfilename == None:
                    missing_fpname.append((part, ' has no fp'))
            except Exception as e:
                missing_files.append((part,e.filename.replace('../Output/test1/testfplib.pretty\\',''),d[part].get("Footprint Completed By")))
        else:
            non_active_parts.append((part, d[part].get(k.status)))

    # pprint.pprint(missing_files)
    # print('\n\n')
    # pprint.pprint(missing_draw)
    # print('\n\n')
    # pprint.pprint(missing_fpname)
    # pprint.pprint(non_active_parts)

    # pprint.pprint(check_repeat_pins(d), width=150)
    print('\n\n')



def get_symbols_with_footprint(d,fpname):
    k = InfoKeys()
    fplist = [part for part in d if d[part].get(k.fp) == fpname]
    return fplist



def check_obsolete(d):
    k = InfoKeys()
    statuslist = []
    for item in d:
        if d[item].get(k.status) != "Active":
            statuslist.append((item, d[item].get(k.status)))
    pprint.pprint(sorted(statuslist, key=lambda x: x[1]))

def check_metadata(d):
    for pn in d:
        partdata = d[pn]
        for key, value in InfoKeys.__dict__.items():
            if not key.startswith("__") and (value != 'parts') and ( value != 'OutputName'): 
                # these part and Output name should be empty, may clean these out later
                if partdata.get(value) in (None,''):
                    print(pn, ' has no ', value)

