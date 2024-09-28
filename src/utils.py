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
    
def form_output(data):
    output = ''
    message_total = 0
    for _, dish in enumerate(data['dishes']):
        output += f"{dish['dish_name']}:\n"
        dish_total = 0
        for ingridient in dish['composition']:
            output += f"  {ingridient['ingridient_name']}: {ingridient['ingridient_mass_in_grams']} грамм - {ingridient['ingridient_callories']} каллорий\n"
            dish_total += int(ingridient['ingridient_callories'])
        output += f"В блюде {dish_total} каллорий\n\n"
        message_total += dish_total
    output += f"Всего {message_total} каллорий"
    return output, message_total