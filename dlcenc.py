#!/usr/bin/python

from Crypto.Cipher import AES
import base64
import binascii

DLC_KEY = binascii.unhexlify("0576DA2C42ED5D7E2972658D23179727A00982D556E077BDE746C326D36A463E")
DLC_IV  = binascii.unhexlify("E5B33881FF8A4960A8B7C7447F3A5F02")

def PAD(bs, s):
	return s + (bs - len(s) % bs) * chr(bs - len(s) % bs)

def UNPAD(s):
	return s[:-ord(s[len(s)-1:])]	

def decodeXml(data):
	data = base64.b64decode(data)
	data = AES.new(DLC_KEY, AES.MODE_CBC, DLC_IV).decrypt(data)
	data = UNPAD(data).decode('utf-8')
	return data

def encodeXml(data):
	data = PAD(len(DLC_KEY), data)
	data = AES.new(DLC_KEY, AES.MODE_CBC, DLC_IV).encrypt(data)
	data = base64.b64encode(data)
	return data

if __name__ == '__main__':
    # example of working with local xml filed
    if False:
        # decoding local file
        fn = 'DLCIndex-v4-35-5-DB313C7522CC127E.xml'
        with open(fn,'rb') as f:
            with open(fn+'.dec','wb') as fo:
                fo.write(decodeXml(f.read()))
    else:
        # example of encoding local xml file
        fn = 'DLCIndex-v4-35-5-DB313C7522CC127E.xml.dec'
        with open(fn,'rb') as f:
            with open(fn+'.enc','wb') as fo:
                fo.write(encodeXml(f.read()))
