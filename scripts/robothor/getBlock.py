def get_block(name, objectType):
    temp = name
    temp = temp.split(' ')[0]
    temp = temp.lower()
    temp = temp.split('_')
    no = ''.join(c for c in temp[-1] if c.isdigit())
    if len(no) == 0: no = '1'
    if (int(no) % 2) == 0:
        no = int(2)  # divisible by 2
    elif (int(no) % 3) == 0:
        no = int(3)  # divisible by 3
    else:
        no = int(1)  # divisible by 1
    item = objectType.lower()
    ans = str(no) + '_' + item
    return ans