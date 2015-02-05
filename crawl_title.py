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


def read_webpage(input_file, newspaper):
    fp = open(input_file, 'r')
    text = fp.read()

    if newspaper == 'udn':
        parser = UdnHTMLParser()
    
    parser.feed(text)

    output_text = parser.print_data()
    return output_text


def remove_empty(data_list):
    remove_list = []
    for data in data_list:
        if data == '':
            remove_list.append(data)

    for item in remove_list:
        data_list.remove(item)

    return data_list


def write_list(output_text, output_file):
    fp = open(output_file, 'w')
    #fp = open(output_file, 'a') #if append
    #fieldnames = ['index', 'date', 'time', 'catalog', 'title', 'link'] #remove index
    fieldnames = ['date', 'time', 'catalog', 'title', 'link']
    output_list = []
    tmp_dict = {}
    
    line_num = 0
    index = 0
    for text in output_text:
        line_mod = line_num % 4
        if line_mod == 0:
            #tmp_dict['index'] = line_num / 4 + 1 #remove index
            tmp_dict['link'] = text
        if line_mod == 1:
            tmp_dict['title'] = text
        if line_mod == 2:
            tmp_dict['catalog'] = text
        if line_mod == 3:
            tmp_dict['date'] = text.split(' ')[0]
            tmp_dict['time'] = text.split(' ')[1]
            output_list.append(tmp_dict)
            tmp_dict = {}
        line_num += 1

    writer = csv.DictWriter(fp, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    for data in output_list:
        writer.writerow(data)

def main():
    parser = argparse.ArgumentParser(description='Crawl the title from realtim news.')
    parser.add_argument('input_file', help='the file name of the html file')
    parser.add_argument('newspaper', help='specify the name of the newspaper')
    args = parser.parse_args()

    #transfer_data(args.input_file)

    #output_file = args.input_file[0:(-1)*len('.html')]+'_list.csv'
    output_file = join('data', args.newspaper+'_list.csv') 

    #output_text = read_webpage('tmp.html', args.newspaper)
    output_text = read_webpage(args.input_file, args.newspaper)
    write_list(remove_empty(output_text), output_file)


if __name__ == '__main__':
    main()
