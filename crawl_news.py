# -*- encoding: utf-8 -*-

##########################################################################
# * This file is used for the thesis of Bamaoo.                          #
# * Extract the news text for a list of news, and save as a folder       #
# * Example of input: (csv file)                                         #
#   - index: 1                                                           #
#   - date: 1/6                                                          #
#   - time: 19:51                                                        #
#   - title: 蔡英文為黃國書站台  送球棒                                  #
#   - link: http://udn.com/NEWS/BREAKINGNEWS/BREAKINGNEWS1/9171701.shtml #
# * Output files:                                                        #
#   1. a csv files contain info from webpage(replace input file)         #
#   2. a floder contains files named by index                            #
# * Example of output: (csv file)                                        #
#   - publisher_info: 【聯合報╱記者蘇木春╱即時報導】                     #
#   - newspaper: 聯合報                                                  #
#   - author: 記者蘇木春                                                 #
#   - article_title: 蔡英文為黃國書站台 送球棒                           #
#   - data from input file                                               #
# * Author: Yu-Ju Chen                                                   #
# * Date: 2015-01-07                                                     #
##########################################################################

import uniout
import argparse
import csv
import os
import time
import pycurl
from pprint import pprint
from HTMLParser import HTMLParser

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

class GetPage:
    def __init__ (self, url):
        self.contents = ''
        self.url = url

    def read_page (self, buf):
        self.contents = self.contents + buf

    def get_page (self):
        return self.contents

    def show_page (self):
        #print self.contents
        return self.contents


class MyHTMLParser(HTMLParser):
    author_tag = False
    title_tag = False
    text_tag = False
    section_tag = False
    span_tag = False
    author = ''
    title = ''
    text = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            for attr in attrs:
                if attr[1] == 'story_author':
                    self.author_tag = True
                elif attr[0] == 'id' and attr[1] == 'story_title':
                    self.title_tag = True
                elif attr[0] == 'id' and attr[1] == 'story':
                    self.text_tag = True

        if tag == 'p' and self.text_tag:
            self.section_tag = True

        if tag == 'span':
            self.span_tag = True

    def handle_endtag(self, tag):
        if tag == 'div' and self.author_tag:
            self.author_tag = False
        if tag == 'div' and self.title_tag:
            self.title_tag = False
        if tag == 'div' and self.text_tag:
            self.text_tag = False
        if tag == 'p' and self.section_tag:
            self.section_tag = False
        if tag == 'span' and self.span_tag:
            self.span_tag = False

    def handle_data(self, data):
        if self.author_tag:
            #self.author =  data.decode('Big5').encode('utf-8')
            self.author = data
            if (data[0:len('【')] == '【') and (data[(-1)*len('】'):] != '】'):
                self.author_tag = False
        
        if self.title_tag:
            #self.title =  data.decode('Big5').encode('utf-8')
            self.title = data
        
        if self.section_tag and not self.span_tag:
            if data.strip():
                self.text += ('\n'+data)

    def print_data(self):
        return self.author, self.title, self.text


def read_input(input_file):
    fp = open(input_file, 'r')
    reader = csv.DictReader(fp, delimiter=';')
    #fieldname = [index, date, time, catalog, title, link]

    data_list = []
    for row in reader:
        data_list.append(row)

    return data_list


def link_webpage(url):
    print url
    time.sleep(2)
    mypage = GetPage(url)
    testcurl = pycurl.Curl()
    testcurl.setopt(testcurl.URL, mypage.url)
    testcurl.setopt(testcurl.WRITEFUNCTION, mypage.read_page)
    testcurl.perform()
    testcurl.close()

    webpage_text = mypage.show_page()
    
    return webpage_text


def parse_webpage(webpage_text):
    text = webpage_text.replace('\r','').decode('Big5hkscs').encode('utf-8')
    parser = MyHTMLParser()
    parser.feed(text)
    webpage_info=parser.print_data()

    return webpage_info

    
# publisher_info example: 
# case 1:【經濟日報╱記者簡威瑟╱即時報導】
#       return (經濟日報, 簡威瑟) 
# case 2:【中央社╱台北16日電】
#       return (中央社, '') 


def parse_publisher_info(publisher_info):
    info = publisher_info[len('【'):(-1)*len('】')].split('╱')

    if len(info) == 3:
        return (info[0], info[1][len('記者'):])
    elif len(info) == 2:
        return (info[0], '')
    else:
        return('error', 'error')


def parse_webpage_list(data_list):
    new_data_list = []

    for data in data_list:
        index = data['index']
        date = data['date']
        time = data['time']
        catalog = data['catalog']
        title = data['title']
        link = data['link']

        webpage_text = link_webpage(link)
        webpage_info = parse_webpage(webpage_text)
        #pprint(webpage_info)
        #webpage_info: [publisher_info, new_title, text]

        publisher_info = webpage_info[0]
        new_title = webpage_info[1]
        text = webpage_info[2]
        (newspaper,author) = parse_publisher_info(publisher_info)

        this_data = {'index': index,
                'date': date,
                'time': time,
                'catalog': catalog,
                'newspaper': newspaper,
                'author': author,
                'title': title,
                'new_title': new_title,
                'text': text,
                'link': link,
                'publisher_info': publisher_info}

        new_data_list.append(this_data)    

    return new_data_list


def write_output(output_data, output_file):
    # output_data[i]: [index, date, time, catalog, newspaper, author, 
    #                 title, new_title, text, link, publisher_info]
    fieldnames = ['index', 'date', 'time', 'catalog', 'newspaper', 
                 'author', 'title', 'new_title', 'same_title', 'link']
    fp = open(output_file, 'w')
    
    writer = csv.DictWriter(fp, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()

    for data in output_data:
        csv_data = data.copy()
        del csv_data['text']
        del csv_data['publisher_info']

        same_title = 'O'
        if csv_data['title'] != csv_data['new_title']:
            same_title = 'X'
        csv_data['same_title'] = same_title

        writer.writerow(csv_data) 


def write_article(news_text, output_file):
    # news_text: [news_title, publisher_info, article, date, time]
    fp = open(output_file, 'w')
    fp.write(news_text['new_title']+'\n')
    fp.write(news_text['date']+' '+news_text['time']+' '+news_text['publisher_info']+'\n')
    fp.write(news_text['text']+'\n')
    #print news_text['text']


def write_folder(output_data, output_folder):
    # note: call write_article for each data
    # note: name the file name as 3 digit, ex: 1 --> 001, 20 --> 020
    # output_data[i]: [index, date, time, catalog, newspaper, author, 
    #                 title, new_title, text, link, publisher_info]
    for data in output_data:
        if int(data['index']) < 10:
            str_index = '00' + str(data['index']) + '.txt'
        elif int(data['index']) < 100:
            str_index = '0' + str(data['index']) + '.txt'
        else:
            str_index = str(data['index']) + '.txt'

        news_info = {'date': data['date'],
                    'time': data['time'],
                    'new_title': data['new_title'],
                    'publisher_info': data['publisher_info'],
                    'text': data['text']}

        file_name = output_folder + '/' + str_index

        write_article(news_info, file_name)


def main():
    parser = argparse.ArgumentParser(description='process input file')
    parser.add_argument('input_file', help='input file')
    args = parser.parse_args()

    output_file = args.input_file[0:(-1)*len('_list.csv')] + '_info.csv'
    output_folder = args.input_file[0:(-1)*len('_list.csv')]
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    data_list = read_input(args.input_file)
    output_data = parse_webpage_list(data_list)
    #pprint(output_data)
    write_output(output_data, output_file)
    write_folder(output_data, output_folder)

if __name__ == '__main__':
    main()
