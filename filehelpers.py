import os, shutil
from partkeys import InfoKeys


def clean_folder(folder):
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)
    print('done cleaning', folder)

# def copy_used_footprints(d, fromdir="../Output/Staging/Footprints", todir = '../Release/digikey-footprints.pretty'):
def copy_used_footprints(d, fromdir, todir):
    """ex  fromdir="../Output/Staging/Footprints", todir = '../Release/digikey-footprints.pretty'"""
    print('copying used footprints')
    k = InfoKeys()
    clean_folder(todir)
    for part in d:
        try:
            if (d[part].get('Include') == "Yes") and (d[part].get(k.fp) != None):
                filename = d[part].get(k.fp) + '.kicad_mod'
                # print(part, filename)
                frompath = os.path.join(fromdir,filename)
                os.makedirs(todir, exist_ok=True)
                shutil.copy2(frompath, todir)
                # print('success-----------------', filename)
            else:
                print(part,'footprint not copied', d[part].get(k.fp), d[part].get('Include'))
        except Exception as e:
            z = d[part]
            print(e, filename, 'not found in ', fromdir, '-----', d[part].get(
                k.fp), 'include', d[part].get('Include'), part)
            # print(d[part])
    print('done copying')

def copy_files(infolder, target_folder):
    #assumes normalized paths
    print('copying files from',infolder, 'to', target_folder)
    file_list = get_kicad_filelist(infolder)
    try:
        target_folder = target_folder
        for file in file_list:
            #             print(file)
            shutil.copy2(file, target_folder)
        print('Done copying footprints to ', target_folder, '\n')
    except Exception as e:
        print(e)

def get_kicad_filelist(infolder):
    ret = []
    nothandled = []
    totalfilecount = 0
    try:
        for file in os.listdir(infolder):
            totalfilecount += 1
            filename = os.fsdecode(file)
            if filename.endswith(".kicad_mod") or filename.endswith(".dcm") or filename.endswith(".lib"):
                ret.append(os.path.join(infolder,filename))
            else:
                nothandled.append(filename)
        print('found ', len(ret), ' out of ',totalfilecount,' total files in ', infolder)
        if len(nothandled) > 0:
            print('\nthese files not handled \n', nothandled)
        return ret
    except Exception as e:
        print(e)

def count_footprints(infolder):
    ret = []
    totalfilecount = 0
    try:
        for file in os.listdir(infolder):
            filename = os.fsdecode(file)
            if filename.endswith(".kicad_mod"):
                totalfilecount += 1
            else:
                print('counting strangeness',filename)
        return totalfilecount
    except Exception as e:
        print(e)