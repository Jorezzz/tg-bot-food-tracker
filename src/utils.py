import base64

def convert_dict_from_bytes(map):
    mydict = dict()
    for keys in map:
        mydict[keys.decode('utf-8')] = map[keys].decode('utf-8')
    return mydict

def convert_list_from_bytes(l):
    return [x.decode('utf-8') for x in l]

def fill_null(x, another):
    if x is None:
        return another
    return x

def encode_image(image):
    return base64.b64encode(image).decode('utf-8')