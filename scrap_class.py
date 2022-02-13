import requests as r
from bs4 import BeautifulSoup
from queue import Queue,Empty
from sys import exit
import threading
from time import sleep
import json

class ScrapGeorgianSynonyms:
    headers = {
        "user-agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
    }
    def __init__(self,url,data={}):
        self.url = url
        self.data = data
        self.wordLinks = []
        self.pagesQueue = Queue()
        self.wordLinksQueue = Queue()
        lastPage = self.findLastPage()
        if lastPage == False:
            print("Invalid url or There is no any page to scrap")
            exit()
        self.createQueue(self.pagesQueue,lastPage)
    @classmethod
    def loadPage(self,url,timeout=15):
        try:
            resp = r.get(url,self.headers,timeout=timeout)
            if resp.status_code == 200:
                return resp
            else:
                return False
        except:
            return False
    def findLastPage(self):
        resp = self.loadPage(self.url)
        if resp:
            soup = BeautifulSoup(resp.text,"html.parser")
            pages = soup.find("div",{"class":"navpages"}).find_all("a")
            tempList = []
            for page in pages:
                try:
                    tempList.append(int(page.text))
                except ValueError:
                    pass
            if len(tempList)>0:
                tempList.sort()
                return tempList[-1]
            return False
        return resp
    @classmethod
    def createQueue(self,pagesQueue,lastPage):
        [pagesQueue.put(page) for page in range(1,lastPage)]
    @classmethod
    def createLinksQueue(self,wordLinksQueue,links):
        [wordLinksQueue.put(link) for link in links]
    def scrapWordLinks(self,resp,wordLinks):
        soup = BeautifulSoup(resp.text,"html.parser")
        termList = soup.find("dl",{"class":"termlist"})
        words = termList.find_all("dt",{"class":"termpreview"})
        definitions = termList.find_all("dd",{"class":"defnpreview"})
        for each in zip(words,definitions):
            if "Synonym" in each[1].text:
                wordLinks.append(each[0].find("a")["href"])
    def collectWordLinks(self,pagesQueue):
        while True:
            try:
                page = pagesQueue.get(False)
                resp = self.loadPage(f"{self.url}&p={page}")
                if resp:
                    self.scrapWordLinks(resp,self.wordLinks)
            except Empty:
                break
    def filterSynonyms(self,text):
        return text.replace("Synonym:","").strip().split(", ")
    def scrapWordSynonyms(self,resp,data):
        soup = BeautifulSoup(resp.text,"html.parser")
        word = soup.find("h1",{"class":"term"})
        synonyms = soup.find("div",{"class":"gwsyn"})
        if word != None:
            if synonyms != None:
                data[word.text] = self.filterSynonyms(synonyms.text)
            else:
                data[word.text] = []
    def collectWordSynonyms(self,wordLinksQueue):
        while True:
            try:
                link = wordLinksQueue.get(False)
                domain = self.url.split("/")[2]
                protocol = self.url.split("://")[0]
                resp = self.loadPage(f"{protocol}://{domain}{link}")
                if resp:
                    self.scrapWordSynonyms(resp,self.data)
            except Empty:
                break
            except Exception as e:
                print(e)
                pass
    @classmethod
    def readDataFromFile(self,fileName):
        with open(fileName,"r",encoding="utf8") as file:
            data = file.read()
            file.close()
        return data.split(",")
    def saveDataAsFile(self,fileName,data):
        with open(fileName,"w",encoding="utf8") as file:
            file.write(",".join(data))
            file.close()
    def saveWordsSynonyms(self,fileName,data):
        with open(fileName,"w",encoding="utf8") as file:
            file.write(json.dumps(data,ensure_ascii=False))
            file.close()
    def monitoring(self):
        print("start")
        while threading.active_count() != 2:
            print(f"Pages left: {self.pagesQueue.qsize()}, collected links {len(self.wordLinks)} active threads: {threading.active_count()}")
            print(f"Links left: {self.wordLinksQueue.qsize()}, collected data {len(self.data)} active threads: {threading.active_count()}\n")
            self.saveDataAsFile("wordLinks.txt",self.wordLinks)
            self.saveWordsSynonyms("wordsSynonyms.json",self.data)
            sleep(2)
    def run(self,threadsQuantity=12):
        threads = []
        synonymCollectThreads = []
        for _ in range(threadsQuantity):
            thread = threading.Thread(target=self.collectWordLinks,args=(self.pagesQueue,))
            thread.start()
            threads.append(thread)
            thread = threading.Thread(target=self.collectWordSynonyms,args=(self.wordLinksQueue,))
            synonymCollectThreads.append(thread)
        threading.Thread(target=self.monitoring,name="Monitoring").start()
        [thread.join() for thread in threads]
        self.saveDataAsFile("wordLinks.txt",self.wordLinks)
        print("start")
        wordLinks = self.readDataFromFile("wordLinks.txt")
        self.createLinksQueue(self.wordLinksQueue,wordLinks)
        [thread.start() for thread in synonymCollectThreads]
        [thread.join() for thread in synonymCollectThreads]
        self.saveWordsSynonyms("wordsSynonyms.json",self.data)
