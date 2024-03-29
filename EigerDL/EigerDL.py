# encoding: utf-8
import time
import sys
from typing import Any
import requests
import pandas as pd
import urllib
import os

class EigerDL:
    def __init__(self):
        self.url = "http://192.168.91.202/data/"
        self.filewriter = "http://192.168.91.202/filewriter/api/1.8.0/files/"

        self.isReadServer = False
        self.isReadLocal = False

    def rmFile(self, filename):
        com = "%s/%s" % (self.url, filename)
        response = requests.delete(com)
        print(response)
    
    def getFile(self, store_dir, filename):
        src = "%s/%s" % (self.url, filename)
        # com = "%s/%s" % (self.filewriter, filename)
        urllib.urlretrieve(src, os.path.join(store_dir, filename))

    def getFiles(self, store_dir, filelist):
        for filename in filelist:
            self.getFile(store_dir, filename)

    def rmFiles(self, filelist):
        for filename in filelist:
            self.rmFile(filename)

    def getSize(self, file_on_server):
        urlpath = "%s/%s" % (self.url, file_on_server)
        u = urllib.urlopen(urlpath)
        file_bytes = float(u.info().getheaders("Content-Length")[0])

        return file_bytes

    def getFilesCurrDir(self, proc_dir):
        import glob
        # processing directoryにあるファイルリストを取得
        files = glob.glob(proc_dir + "/*")

        # files にあるファイルのサイズを確認する
        # self.localFiles という辞書にファイル名とサイズを格納
        self.localFiles = {}
        for filename in files:
            # print(filename)
            fsize = os.path.getsize(filename)
            # filename の最後の / 以降の文字列をファイル名として登録する
            self.localFiles[filename.split("/")[-1]] = fsize
        self.isReadLocal = True

    def getFilesLocalWithPrefix(self, proc_dir, prefix):
        self.getFilesCurrDir(proc_dir)
        # getFilesCurrDir() で取得した self.localFiles から prefix で始まるもの以外を削除する
        # 辞書として作成
        self.filesLocalWithPrefix = {}
        for filename in self.localFiles:
            if filename.startswith(prefix):
                self.filesLocalWithPrefix[filename] = self.localFiles[filename]

        return self.filesLocalWithPrefix

    def updateServerInfo(self):
        filelist = self.getList()
        # self.serverFiles という辞書にファイル名とサイズを格納
        self.serverFiles = {}
        for filename in filelist:
            fsize = self.getSize(filename)
            self.serverFiles[filename] = fsize
        self.isReadServer = True
    
    def getFileListOnServerWithPrefix(self, prefix):
        if self.isReadServer == False:
            self.updateServerInfo()
        # updateServerInfo() で取得した self.serverFiles から、prefix で始まるファイル名のリストを作成する
        # 作成するのは辞書
        self.filesOnServerWithPrefix = {}
        for filename in self.serverFiles:
            if filename.startswith(prefix):
                self.filesOnServerWithPrefix[filename] = self.serverFiles[filename]

        return self.filesOnServerWithPrefix

    def getManipulateList(self, listServer, listLocal):
        # dictionary listServer, listLocal
        # 両方にあり、さらに、ファイルサイズも同じものを削除対象とする
        # そうでないものはダウンロード対象とする
        download_list = []
        delete_list = []
        for filename in listServer:
            if filename in listLocal:
                if listServer[filename] == listLocal[filename]:
                    delete_list.append(filename)
                else:
                    download_list.append(filename)
            else:
                download_list.append(filename)

        return delete_list, download_list
    
    def getList(self):
        response = requests.get(self.filewriter)
        listjson=response.json()

        # listjson からファイル名を取得
        filelist=listjson['value']
        
        return filelist

    def normalProc(self, prefix, isRemove=True):
        s_list = self.getFileListOnServerWithPrefix(prefix)
        # print("server:", s_list)
        # prefix のディレクトリを作成する
        # ディレクトリ構造は prefix/scan/ とする
        dir_to_be_checked = prefix + "/scan/"
        if not os.path.exists(dir_to_be_checked):
            os.makedirs(dir_to_be_checked)
        else:
            print("making directory is skipped")

        l_list = self.getFilesLocalWithPrefix(dir_to_be_checked, prefix)

        rmlist,dllist = self.getManipulateList(s_list, l_list)
        print("To be downloaded:", dllist)
        print("To be deleted:",rmlist)
        self.getFiles(dir_to_be_checked, dllist)
        if isRemove:
            self.rmFiles(rmlist)
        else:
            print("No files are removed from 'isRemove'")

    def getPrefixListOnServer(self):
        file_list = self.getList()
        prefix_list = []
        for f in file_list:
            if "master" in f:
                #_master 以前までをprefixとして取得
                prefix = f.split("_master")[0]
                prefix_list.append(prefix)
        
        return prefix_list
