#!/usr/bin/env python

#author: wowdd1
#mail: developergf@gmail.com
#data: 2014.12.07

from spider import *

class GithubSpider(Spider):
    lang_list = [
        "C",
        "C++",
        "C#",
        "Clojure",
        "CoffeeScript",
        "Common Lisp",
        "CSS",
        "D",
        "Dart",
        "Emacs Lisp",
        "Erlang",
        "F#",
        "Go",
        "Haskell",
        "Java",
        "JavaScript",
        "Julia",
        "Lua",
        "Matlab",
        "Objective-C",
        "Perl",
        "PHP",
        "Python",
        "R",
        "Ruby",
        "Scala",
        "Scheme",
        "Shell",
        "SQL",
        "Swift"]

    result = ""
    request_times = 0
    def __init__(self):
        Spider.__init__(self)
        self.school = "github"

    def isQueryLang(self, lang):
        for item in self.lang_list:
            if item.lower() == lang.lower():
                return True
        return False

    def getUrl(self, lang, page, large_than_stars, per_page):
        if self.isQueryLang(lang) == True:
            return "https://api.github.com/search/repositories?page=" + str(page) + "&per_page=" + per_page + "&q=stars:>" + large_than_stars +"+language:" +  lang.replace("#","%23").replace("+","%2B") + "&sort=stars&order=desc"
        else:
            return "https://api.github.com/search/repositories?page=" + str(page) + "&per_page=" + per_page + "&q=" + lang + "+stars:>" + large_than_stars + "&sort=stars&order=desc"

    def checkRequestTimes(self):
        self.request_times += 1
        if self.request_times % 10 == 0:
            print "wait 60s..."
            time.sleep(60) 

    def processPageData(self, f, file_name, lang, url):
        self.checkRequestTimes()
        #print "url: " + url
        r = requests.get(url)
        dict_obj = json.loads(r.text)
        total_size = 0
        for (k, v) in dict_obj.items():
            if k == "total_count":
                total_size = v
            if k == "message":
                print v
                self.result += lang + " "
                self.cancel_upgrade(file_name)
                return
            if k == "items":
                for item in v:
                    data = str(item['stargazers_count']) + " " + item["name"] + " " + item['html_url']
                    print data
                    description = ""
                    if item['description'] != None:
                        description = item['description'] + " (author:" + item['owner']['login'] + " stars:" + str(item["stargazers_count"]) + " forks:" + str(item['forks_count']) + " watchers:" + str(item['watchers']) + ")"
                    self.write_db(f, str(item["stargazers_count"]) + "-" + str(item['forks_count']), item["name"], item['html_url'], description)
                    self.count = self.count + 1
        return total_size

    def processGithubData(self, lang, large_than_stars, per_page):
        file_name = self.get_file_name("eecs/github/" + lang, self.school)
        file_lines = self.countFileLineNum(file_name)
        f = self.open_db(file_name + ".tmp")
        page = 1
        url = self.getUrl(lang, page, str(large_than_stars), str(per_page))
        self.count = 0

        print "processing " + lang
 
        total_size = self.processPageData(f, file_name, lang, url)
        if total_size > 1000:
            total_size = 1000
        while total_size > (page *per_page):
            #print "total size:" + str(total_size) + " request page 2"
            page += 1
            self.processPageData(f, file_name, lang, self.getUrl(lang, page, str(large_than_stars), str(per_page)))
     
        self.close_db(f)
        if self.count > 0:
            self.do_upgrade_db(file_name)
            print "before lines: " + str(file_lines) + " after update: " + str(self.count) + " \n\n"
        else:
            self.cancel_upgrade(file_name)
            print "no need upgrade\n"

    def getUserUrl(self, location, followers, per_page):
        if location == "":
            return "https://api.github.com/search/users?page=1&per_page=" + per_page + "&q=followers:>" + followers
        else:
            return "https://api.github.com/search/users?page=1&per_page=" + per_page + "&q=followers:>" + followers + "+location:" + location



    def processGithubiUserData(self, location, followers, per_page):
        self.checkRequestTimes()
        file_name = self.get_file_name("eecs/github/" + location, self.school + "-user")
        file_lines = self.countFileLineNum(file_name)
        f = self.open_db(file_name + ".tmp")

        url = self.getUserUrl(location, str(followers), str(per_page))
            
        print "processing " + url
        r = requests.get(url)
        dict_obj = json.loads(r.text)
        self.count = 0
        for (k, v) in dict_obj.items():    
            if k == "items":
                for item in v:
                    data = str(item["id"]) + " " + item["login"] + " " + item["url"]
                    print data
                    self.write_db(f, item["type"] + "-" + str(item["id"]), item["login"], item["url"])
                    self.count = self.count + 1

        self.close_db(f)
        if self.count > 0:
            self.do_upgrade_db(file_name)
            print "before lines: " + str(file_lines) + " after update: " + str(self.count) + " \n\n"
        else:
            self.cancel_upgrade(file_name)
            print "no need upgrade\n"

    def do_work(self):
        for lang in self.lang_list:
            self.processGithubData(lang, 500, 100)

        if len(self.result) > 1:
            print self.result + " is not be updated"

        print "get spark data..."
        self.processGithubData("spark", 500, 100)

        print "get user data..."
        self.processGithubiUserData("", 1000, 50)
        self.processGithubiUserData("china", 1000, 50)
        
        
start = GithubSpider()
start.do_work()