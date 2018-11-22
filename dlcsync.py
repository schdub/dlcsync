#!/usr/bin/python

import xml.etree.ElementTree as ET
import binascii
import urllib2
import zipfile
import io
import os

verbose = False        # display some debug messages
showOnly = False       # only show the list of files that need to be loaded
removeTempFiles = True # delete temp file after unzipping its content
lang = [ 'all', 'en' ] # en,fr,it,de,es,ko,zh,cn,pt,ru,tc,da,sv,no,nl,tr,th
tier = [ 'all', '25' ] # 25,50,100,retina,iphone,ipad,ipad3
LOCAL_DLC_DIR = '~/dlc/' # directory where DLC will be loaded
URL_DLC_BASE  = 'http://oct2018-4-35-0-uam5h44a.tstodlc.eamobile.com/netstorage/gameasset/direct/simpsons/'

def LOG(msg):
	if verbose: print(msg)

def crc32ForFile(filename):
	with open(filename,'rb') as f:
		buf = (binascii.crc32(f.read()) & 0xFFFFFFFF)
		return "%d" % buf

def getZippedXml(url):
	r = urllib2.urlopen(url)
	data = r.read()
	r.close()
	LOG("downloaded %d bytes" % len(data))
	with zipfile.ZipFile(io.BytesIO(data)) as z:
		data = z.read(z.infolist()[0])
		LOG("unzipped %d bytes" % len(data))
		return data

def getDlcIndex():
	tree = ET.fromstring(getZippedXml(URL_DLC_BASE + 'dlc/DLCIndex.zip'))
	lst = tree.findall('./IndexFile')
	return lst[0].get('index').replace(':', '/')

def getRest(dlFile, fromUrl):
	existSize = 0
	req = urllib2.Request(fromUrl)
	if os.path.exists(dlFile):
		outputFile = open(dlFile, "ab")
		existSize = os.path.getsize(dlFile)
		# if the file exists, then download only the remainder
		req.headers['Range'] = 'bytes=%s-' % (existSize)
	else:
		outputFile = open(dlFile,"wb")
	webPage = urllib2.urlopen(req)
	if verbose:
		for k, v in webPage.headers.items():
			LOG("%s=%s" % (k, v))
	# if we already have the whole file, there is no need to download it again
	ok = False
	numBytes = 0
	webSize = int(webPage.headers['Content-Length'])
	if webSize == existSize:
		LOG("File (%s) was already downloaded from URL (%s)" % (dlFile, fromUrl))
		ok = True
	else:
		#LOG("Downloading %d more bytes" % (webSize-existSize))
		while 1:
			data = webPage.read(8192)
			if not data: break
			outputFile.write(data)
			numBytes = numBytes + len(data)
		ok = numBytes == webSize
		LOG("downloaded %d bytes from %d" % (numBytes, webSize))
	webPage.close()
	outputFile.close()
	return ok

def doDownload(fn):
	print(fn)
	if showOnly: return

	tempFileName = fn.replace('/', '#')
	bytesCount = getRest(tempFileName, URL_DLC_BASE + fn)
	with zipfile.ZipFile(tempFileName) as z:
		localPath = LOCAL_DLC_DIR + fn[:-4] + '/'
		z.extractall(localPath)

	if removeTempFiles: os.remove(tempFileName)

class DlcIndexParser:
	ignorePackage = True
	# called for each opening tag.
	def start(self, tag, attrib):
		#LOG("tag='%s' attrib='%s'" % (tag, attrib))
		if (tag == 'Package'):
			# initilize variables for each Package
			self.ignorePackage = False
			self.LocalDir = ''
			self.FileSize = ''
			self.UncompressedFileSize = ''
			self.IndexFileCRC = ''
			self.IndexFileSig = ''
			self.Version = ''
			self.FileName = ''
			self.Language = ''
			if attrib['ignore'] == 'true' or attrib['tier'] not in tier:
				self.ignorePackage = True
		# ignore?
		if (self.ignorePackage):
			return
		# parse sub-tag for Package
		if (tag == 'LocalDir'):
			self.LocalDir = attrib['name']
		elif (tag == 'FileSize'):
			self.FileSize = attrib['val']
		elif (tag == 'UncompressedFileSize'):
			self.UncompressedFileSize = attrib['val']
		elif (tag == 'IndexFileCRC'):
			self.IndexFileCRC = attrib['val']
		elif (tag == 'IndexFileSig'):
			self.IndexFileSig = attrib['val']
		elif (tag == 'Version'):
			self.Version = attrib['val']
		elif (tag == 'FileName'):
			self.FileName = attrib['val']
		elif (tag == 'Language'):
			self.Language = attrib['val']
	# called for each closing tag.
	def end(self, tag):
		if (tag == 'Package'):
			if (not self.ignorePackage and self.Language in lang):
				need2Download = True
				fn = self.FileName.replace(':', '/')
				zeroFile = LOCAL_DLC_DIR + fn[:-4] + '/0'
				# check crc32 of local 0 file
				if os.path.exists(zeroFile):
					crc32 = crc32ForFile(zeroFile)
					need2Download = crc32 != self.IndexFileCRC
					if need2Download:
						print("crc mismatch actual=%s expected=%s." % (crc32, self.IndexFileCRC))
				# now download it
				if need2Download:
					doDownload(fn)
			self.ignorePackage = True
	def data(self, data): pass
	def close(self): pass

if __name__ == '__main__':
	LOCAL_DLC_DIR = os.path.expanduser(LOCAL_DLC_DIR)
	if LOCAL_DLC_DIR[-1] != '/': LOCAL_DLC_DIR = LOCAL_DLC_DIR + '/'
	index = getDlcIndex()
	print(index)
	parser = ET.XMLParser(target=DlcIndexParser())
	parser.feed(getZippedXml(URL_DLC_BASE + index))
	parser.close()
