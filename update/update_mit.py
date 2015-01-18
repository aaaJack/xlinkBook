#!/usr/bin/env python
    
#author: wowdd1
#mail: developergf@gmail.com
#data: 2014.12.07
from spider import *
from update_mit_ocw import MitOcwSpider

class MitSpider(Spider):
    ocw_links = {}
 
    def __init__(self):
        Spider.__init__(self)    
        self.school = "mit"
        self.subject = "eecs"
        self.ocw_spider = MitOcwSpider()
        self.deep_mind = True
   
    def initOcwLinks(self):
        r = requests.get('http://ocw.mit.edu/courses/electrical-engineering-and-computer-science/')
        soup = BeautifulSoup(r.text)
        i = 0
        course_num = ''
        link = ''
        for a in soup.find_all("a", class_="preview"):
            i = i + 1
            if i == 1:
                course_num = a.string.replace("\n", "").strip()
                link = 'http://ocw.mit.edu' + str(a["href"])
                if self.ocw_links.get(course_num, '') == '':
                    self.ocw_links[course_num] = link
            if i >= 3:
                i = 0

    def getTextBook(self, course_num):
        terms = ['2014SP', '2013SP', '2012SP']
        for term in terms:
            r = requests.get('http://eduapps.mit.edu/textbook/books.html?Term=' + term + '&Subject=' + course_num)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text)
                table = soup.find('table', class_='displayTable')
                if table == None:
                    continue
                splits = table.text.strip()[table.text.strip().find('Price') + 6 :].strip().split('\n')
                if splits[0] == 'Course Has No Materials':
                    continue
                return 'textbook:' + splits[1] + ' (' + splits[0] + ')' + ' '
        return ''

    def getMitCourseLink(self, links, course_num):
        if course_num == "":
            return course_num
        if self.ocw_links.get(course_num, '') != '':
            return self.ocw_links[course_num]

        for link in links:
            if link.attrs.has_key("href") and link["href"].find(course_num) != -1 and link["href"].find("editcookie.cgi") == -1:
                return link["href"]
        return ""
        
    def clearHtmlTag(self, html):
        while(html.find('<') != -1 and html.find('>') != -1):
            html = html.replace(html[html.find('<') : html.find('>') + 1], '')
        return html
    
    def processMitData(self, html, f):
        if self.need_update_subject(self.subject) == False:
            return
        #print html
        soup = BeautifulSoup(html);
        links_all = soup.find_all("a")
        course_links = []
        for link in links_all:
            if link.attrs.has_key("href") and False == link["href"].startswith("editcookie.cgi") \
               and False == link["href"].startswith("/ent/cgi-bin") and False == link["href"].startswith("javascript:") \
               and False == link["href"].startswith("m"):
                course_links.append(link)
        course_num = ""
        title = ""
        link = ""
        textbook = ''
        prereq = ''
        instructors = ''
        for line in html.split("\n"):

            if (line.strip().startswith('<br>') and self.clearHtmlTag(line.strip())[1 : 2] == '.') or \
                line.find('Prereq:') != -1:
                if line.find('Prereq:') != -1:
                    prereq = self.clearHtmlTag(line).lower() + ' '
                if line.strip().startswith('<') and self.clearHtmlTag(line.strip())[1 : 2] == '.':
                    instructors = 'instructors:' + self.clearHtmlTag(line.strip()[0 : line.strip().find('</')]) + ' '

            if line.strip().find('<h3>') != -1 or \
                (line.strip().startswith('<br>') and (line.strip()[len(line.strip()) - 1 : ] == '.' or line.strip()[len(line.strip()) - 7 : ] == 'limited')):
                line = line[line.find('>', 3) + 1 : ]
                if line.find('</h3>') == -1:
                    #print line
                    if line[0 : 2] == '6.':
                        if course_num != '':
                            print course_num + " " + title + " " + link                     

                            if instructors != '' and remark.find('instructors:') == -1:
                                remark = instructors + ' ' + remark

                            self.count = self.count + 1
                            self.write_db(f, course_num, title, link, remark)
                            remark = ''
                            course_num = ""
                            title = ""
                            link = ""
                            textbook = ''
                            pereq = ''
                            instructors = ''

                        course_num = line.strip()[0 : line.strip().find(" ")]
                        textbook = ''
                        if self.deep_mind:
                            textbook = self.getTextBook(course_num)

                        if textbook == '' and self.deep_mind and self.ocw_links.get(course_num, '') != '':
                            textbook = self.ocw_spider.getTextBook(self.ocw_links[course_num], course_num)
 
                        title = line.strip()[line.strip().find(" ") + 1 : ]
                        if course_num.find(',') != -1:
                            course_num = line.strip()[0 : line.strip().find(" ", line.strip().find(" ") + 1)]
                            title = line.strip()[line.strip().find(" ", line.strip().find(" ") + 1) + 1 : ]
                        link = self.getMitCourseLink(course_links, course_num.strip())
                    else:
                        remark = ''
                        if self.deep_mind and self.ocw_links.get(course_num, '') != '':
                            remark = self.ocw_spider.getDescription(self.ocw_spider.getDescriptionApiUrl(self.ocw_links[course_num]))
                            if remark.find('description:') != -1:
                                remark = remark[0 : remark.find('description:')]

                        if textbook != '':
                            remark += textbook
                        if prereq != '':
                            remark += prereq

                        remark += 'description:' + line.strip() + ' ' 
        if course_num != '':
            self.count = self.count + 1
            self.write_db(f, course_num, title, link, remark)

    def doWork(self):
        #mit
        #"""
        print 'init ocw course links'
        self.initOcwLinks()

        print "downloading mit course info"
        file_name = self.get_file_name(self.subject, self.school)
        file_lines = self.countFileLineNum(file_name)
        f = self.open_db(file_name + ".tmp")
        self.count = 0
 
        r_a = requests.get("http://student.mit.edu/catalog/m6a.html")
        r_b = requests.get("http://student.mit.edu/catalog/m6b.html")
        r_c = requests.get("http://student.mit.edu/catalog/m6c.html")
    
    
        print "processing html and write data to file..."
        self.processMitData(r_a.text, f)
        self.processMitData(r_b.text, f)
        self.processMitData(r_c.text, f)
     
    
        self.close_db(f)
        if file_lines != self.count and self.count > 0:
            self.do_upgrade_db(file_name)
            print "before lines: " + str(file_lines) + " after update: " + str(self.count) + " \n\n"
        else:
            self.cancel_upgrade(file_name)
            print "no need upgrade\n"
        #"""
   
start = MitSpider()
start.doWork() 
