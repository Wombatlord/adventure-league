import hashlib

disallowed = [
    b'\x99\x15\xba-\x82"\x80\xf2,(=\xf4\xe7e\x84\xa4\x0e\x01\x19\xfcX\xf7<_\x84\xd4\xfd\xb0M\x04\xfao',
    b"})i\xe3z\xa4\xff`0\xee[[\x9e`\xf8h\x9a[\xab\nJ$\xb42\xd7\xeeK\xe1W\xe5\xf6\xbd",
    b"Xj\xcb<k\xacH\x93\x08\xc0\x93\x8fv-\xa7\x02W:qM\xfd\xf3\xa7)\xdc\xb4\x07X\xb4\xc3c\xae",
    b"\x98\xd4N\x13\xf4U\xd9\x16gM8BM9\xe1\xcb\x01\xb2\xa9\x13*\xac\xbb{\x97\xa6\xf8\xbb\x7f\xeb%D",
    b"YH\x10\xad\xcb\xee \xbd\x1do\x8eL\xeeQ\xef\xdf\x1a#V\x91\xe9\xd0\x8f\xe9l\xe9D\xd7\xfd\xe3O\xd6",
    b"\x04\xdd\xcfX\xed,\r`9\xe2N\xd1\x1e'\\+\x82p\xbc\xc2\xf4\x9f\xc7hZc\x88\xb8\x05Z\x02\x99",
    b"\xbb\x06\x89\xe3\x99\xcc\xa9\xd9\x02\x83\x11-s\xaal\x89\x99S\xc4\xc3\xcb\xd3\x9a<\x08{c\xde9\xf3\x04\xaa",
    b"c\xca B\xe7\xef%\x10\xae\xb0j\x0b\xba\xd7\xbdmD`5`\xf6\xe3\x92V[\x9a\xe8c\x829\xa2\xd3",
    b"\x98%Z(\x8b\xd2\xde\x15\x18\xd0\xa7\x14\x0cL\xb1\xd7(T\x0f\xe9l\x04\xbd'\x17.:\xf46\x8a\x96)",
]

def constrained_bytes():
    byte_array = []
    with open("C:/Users/Owner/Code/PythonProjects/adventure_league/src/utils/proc_gen/file") as disallowed_bytes:
        lines = disallowed_bytes.split("\n")
        
        for byte in disallowed_bytes:
            byte_array.append(byte)

    return byte_array
    
def check(s: str, disallowed_list:list|None=None) -> bool:
    global disallowed
    if disallowed_list is None:
        disallowed_list = disallowed
    
    constraints = constrained_bytes()
    
    # print(constraints)
    combined = "".join(s)
    final = combined.lower()
    
    return allowed_token(final, constraints)
    
def allowed_token(s, disallowed_list):
    as_bytes = str.encode(s)
    hashed = hashlib.sha256(as_bytes)
    if hashed.digest() in disallowed_list:
        print("BAD")
        return False
    else:
        return True
