#!/usr/bin/python

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import os, sha, base64, tarfile, re

def get_dcp_directory():
    return '/mnt/space/interfaces/in_ftp/SmartDCP'

def get_dcp_workdir():
    return '/mnt/space/interfaces/in_ftp/.workdir/SmartDCP'

def get_input_dcps():
    """ Return a dirpath list of all input DCP """

    dirlist = []
    try:
        files = os.listdir(get_dcp_workdir())
        for file in files:
            path = os.path.join(get_dcp_workdir(), file)
            if os.path.isdir(path):
                dirlist.append(path)
    except:
        pass

    return dirlist

def dcp_create_tar(dirpath):
    # Create a tar of all non mxf files or directory and return the tar filename (or None)
    try:
        tar_path = os.path.join(dirpath, os.path.basename(dirpath)) + ".tar"
        tar = tarfile.open(tar_path, 'w')
        files = os.listdir(dirpath)
        for file in files:
            if file == "INGEST_IT":
                continue
            ext = os.path.splitext(file)[1]
            if ext != ".mxf" and ext != ".md5" and ext != ".hash":
                tar.add( os.path.join(dirpath, file), file )
        tar.close()
        return tar_path
    except Exception, error:
        return None

def dcp_create_ingest_demand_file(dcpname):
    path = os.path.join(get_dcp_workdir(), dcpname, 'INGEST_IT')
    try:
        fd = open(path, 'w')
        fd.close()
    except:
        return False
    else:
        return True

def get_dcp_hash_file(path):
    hash = ''
    try:
        hash = open(path + '.hash', 'r').readline()
    except:
        sh = sha.new()
        fd = open(path, 'r')
        buf = fd.read(16384)
        while buf:
            sh.update(buf)
            buf = fd.read(16384)

        hash = base64.encodestring(sh.digest())
        hash = hash[:-1] # delete the carriage return...
        try:
            fd = open(path + '.hash', 'w')
            fd.write(hash)
        except:
            pass

    return hash

# AssetMap : XML Parsing Class (SAX)
class AssetMapHandler(ContentHandler):
    def __init__(self, files, pklsList):
        self.tmp_id = ''
        self.isPackingList = False
        self.buf = ''
        self.files = files
        self.pklsList = pklsList
    def startElement(self, name, attrs):
        self.buf = ''
    def endElement(self, name):
        if name == 'Id':
            self.tmp_id = self.buf
        if name == 'PackingList':
            self.isPackingList = True
        elif name == 'Path':
            if self.buf.startswith('file:///'):
                self.buf = self.buf[8:]
            self.files[self.tmp_id] = [self.buf, None, None, None]
            if self.isPackingList:
                self.pklsList[self.tmp_id] = self.buf
            self.isPackingList = False
    def characters(self, ch):
        self.buf += ch

# PackingFile : XML Parsing Class (SAX)
class PklHandler(ContentHandler):
    def __init__(self, files):
        self.tmp_id = ''
        self.buf = ''
        self.files = files
    def startElement(self, name, attrs):
        self.buf = ''
    def endElement(self, name):
        if name == 'Id':
            self.tmp_id = self.buf
        elif name == 'Hash':
            try:
                self.files[self.tmp_id][1]= self.buf
            except:
                pass
    def characters(self, ch):
        self.buf += ch

def get_dcp_infos(dirpath):
    """ Search the ASSETMAP.xml and all needed files of a DCP
    Return three object :
    - boolean : True if DCP is complete
    - boolean : True if DCP is valid (correct hash values)
    - dictionnay : all files needed ( { id : [filename, hash, found, correct_hash] } )

    If dictionnary is empty, maybe the ASSETMAP file was not found"""

    pklsList = {} 
    files = {}

    # ASSETMAP.xml contain all files informations
    assetmap_list = ( 'ASSETMAP', 'ASSETMAP.xml', 'ASSETMAP.XML', 'assetmap', 'assetmap.xml' )
    txt = ""
    found = False
    for assetmap in assetmap_list:
        assetmap_path = os.path.join (dirpath, assetmap)
        if not os.path.isfile( assetmap_path ):
            continue
        try:
            file = open(assetmap_path, 'r')
            txt = file.read()
        except IOError, inst:
            continue
        else:
            found = True
            break

    if not found:
        return False, False, files

    # We search all files needed by the DCP (write it in 'files' variable)
    doc = AssetMapHandler(files, pklsList)
    saxparser = make_parser()
    saxparser.setContentHandler(doc)

    datasource = open(assetmap_path,"r")
    saxparser.parse(datasource)

    # We find the hash for each file (in PKL files)
    doc = PklHandler(files)
    saxparser.setContentHandler(doc)

    for id in pklsList.keys():
        try:
            datasource = open( os.path.join(dirpath, pklsList[id]), "r" )
            saxparser.parse(datasource)
            files[id][3] = files[id][2] = True
        except:
            pass

    # We check if the hash is valid
    error = False
    for id in files.keys():
        filepath = os.path.join(dirpath, files[id][0])
        if not os.path.isfile(filepath):
            files[id][2] = False
            error = True
        else:
            files[id][2] = True
            hash = get_dcp_hash_file(filepath)
            if files[id][1] == hash:
                files[id][3] = True
            elif files[id][1] and id not in pklsList.keys():
                files[id][3] = False
    if error:
        return False, False, files
    else:
        # We check the validity of the DCP
        valid = True
        for id in files.keys():
            if not files[id][3]:
                valid = False
        return True, valid, files

