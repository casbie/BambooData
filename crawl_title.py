#-*- coding: utf-8 -*-

#############################################################
# * parse realtime news title from given webpage            #
# * Input: [date].html [newspaper]                          #
#   [newspaper]: apple chinatimes ettoday ltn udn           #
# * Output: [date]_list.csv                                 #
# * Author: Yu-Ju Chen                                      #
# * Date: 2015-01-06 created                                #
#         2015-02-05 modified                               #
#############################################################


import sys
import os
import csv
import argparse
import codecs
import pycurl
import uniout
from os.path import join
from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint
from pprint import pprint


def delete_same(noun_list):
    seen=[]
    for n in noun_list:
        if n not in seen:
            seen.append(n)
    return seen


def transfer_data(data_path):
    # tell codecs the encoding of file
    #with codecs.open(fpath, encoding='big5') as f:
    with codecs.open(data_path, encoding='big5', errors='ignore') as f:
        content = f.read()
        # now content is utf-8 encoded

    # replace encoding declaration
    content = content.replace('encoding="Big5"', 'encoding="utf-8"', 1)

    with codecs.open('tmp.html', 'wb', encoding='utf-8') as f:
        f.write(content)


class AppleHTMLParser(HTMLParser):
    data_list = []
    news_tag = False
    title_tag = False
    time_tag = False
    categ_tag = False
    url = ''
    date = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'time':
            self.time_tag = True
        if tag == 'li' and len(attrs) == 1:
            if attrs[0][0] == 'class':
                self.news_tag = True
        if tag == 'h2' and self.news_tag:
            self.categ_tag = True
        if tag == 'font' and self.news_tag:
            self.title_tag = True
        if tag == 'a' and self.news_tag:
            if len(attrs) > 1 and attrs[0][0] == 'href':
                self.url = 'http://www.appledaily.com.tw' + attrs[0][1]
                self.data_list.append(self.url)

    def handle_endtag(self, tag):
        if tag == 'time' and self.time_tag:
            self.time_tag = False
        if tag == 'li' and self.news_tag:
            self.news_tag = False
        if tag == 'h2' and self.categ_tag:
            self.categ_tag = False
        if tag == 'font' and self.title_tag:
            self.title_tag = False

    def handle_data(self, data):
        if self.time_tag:
            if data[0:4] == '2015':
                year = data.split(' / ')[0]
                month = data.split(' / ')[1]
                day = data.split(' / ')[2]
                self.date = month + '/' + day
            else:
                self.data_list.append(self.date + ' ' + data)
        if self.categ_tag:
            self.data_list.append(data)
        if self.title_tag:
            self.data_list.append(data)
    
    def print_data(self):
        return self.data_list
    
    def clear_data(self):
        del self.data_list[:]
        self.news_tag = False
        self.title_tag = False
        self.date_tag = False
        self.categ_tag = False
        self.url = ''
        self.date = ''

class UdnHTMLParser(HTMLParser):
    data_list = []
    news_tag = False
    title_tag = False
    date_tag = False
    categ_tag = False
    url = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            for attr in attrs:
                if attr[0] == 'style' and attr[1] == 'table-row':
                    self.news_tag = True
        if tag == 'a' and self.news_tag:
            for attr in attrs:
                if attr[0] == 'href':
                    self.url = 'http://udn.com' + attr[1]
                    self.data_list.append(self.url)
                    self.title_tag = True
        if tag == 'td' and self.news_tag:
            if len(attrs) == 2:
                if attrs[0][1] == 'only_web' and attrs[1][1] == 'center':
                    self.categ_tag = True
                if attrs[0][1] == 'right' and attrs[1][1] == 'only_web':
                    self.date_tag = True

    def handle_endtag(self, tag):
        if tag == 'tr' and self.news_tag:
            self.news_tag = False
        if tag == 'a' and self.title_tag:
            self.title_tag = False
        if tag == 'td':
            if self.categ_tag:
                self.categ_tag = False
            elif self.date_tag:
                self.date_tag = False

    def handle_data(self, data):
        if self.news_tag and self.title_tag:
            self.data_list.append(data.strip())
        if self.news_tag and self.categ_tag:
            self.data_list.append(data.strip())
        if self.news_tag and self.date_tag:
            self.data_list.append(data.strip())
      
    def print_data(self):
        return self.data_list
    
    def clear_data(self):
        del self.data_list[:]
        self.news_tag = False
        self.title_tag = False
        self.date_tag = False
        self.categ_tag = False
        self.url = ''


def read_webpage(input_file, newspaper):
    fp = open(input_file, 'r')
    text = fp.read()

    if newspaper == 'udn':
        parser = UdnHTMLParser()
    elif newspaper == 'apple':
        parser = AppleHTMLParser()

    parser.feed(text)

    output_text = parser.print_data()[:]
    parser.clear_data()
    return output_text


def remove_empty(data_list):
    remove_list = []
    for data in data_list:
        if data == '':
            remove_list.append(data)

    for item in remove_list:
        data_list.remove(item)

    return data_list


def write_list(output_text, output_file, newspaper):

    fp = open(output_file, 'w')
    #fp = open(output_file, 'a') #if append
    #fieldnames = ['index', 'date', 'time', 'catalog', 'title', 'link'] #remove index
    fieldnames = ['date', 'time', 'catalog', 'title', 'link']
    output_list = []
    tmp_dict = {}
    
    #line_mod: [0]link [1]title [2]catalog [3]date&time
    if newspaper == 'udn':
        line_header = [0, 1, 2, 3]
    elif newspaper == 'apple':
        line_header = [0, 3, 2, 1]

    line_num = 0
    index = 0
    for text in output_text:
        line_mod = line_num % 4
        if line_mod == line_header[0]:
            #tmp_dict['index'] = line_num / 4 + 1 #remove index
            tmp_dict['link'] = text
        if line_mod == line_header[1]:
            tmp_dict['title'] = text
        if line_mod == line_header[2]:
            tmp_dict['catalog'] = text
        if line_mod == line_header[3]:
            tmp_dict['date'] = text.split(' ')[0]
            tmp_dict['time'] = text.split(' ')[1]
        if line_mod == 3:
            output_list.append(tmp_dict)
            tmp_dict = {}
        line_num += 1

    output_list = delete_same(output_list)
    pprint(output_list)
    writer = csv.DictWriter(fp, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    for data in output_list:
        writer.writerow(data)

def main():
    parser = argparse.ArgumentParser(description='Crawl the title from realtim news.')
    parser.add_argument('input_folder', help='the folder name of the html files')
    parser.add_argument('newspaper', help='specify the name of the newspaper')
    args = parser.parse_args()

    #transfer_data(args.input_file)
    #output_text = read_webpage('tmp.html', args.newspaper)

    #output_file = args.input_file[0:(-1)*len('.html')]+'_list.csv'
    output_file = args.input_folder + '_list.csv'

    files = [f for f in os.listdir(args.input_folder) if os.path.isfile(join(args.input_folder, f))] 
    output_text = []
    for f in files:
        tmp_text = read_webpage(join(args.input_folder, f), args.newspaper)
        output_text = output_text + tmp_text
   
    write_list(remove_empty(output_text), output_file, args.newspaper)


if __name__ == '__main__':
    main()
