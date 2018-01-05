#!Python3
# -*- coding:utf-8 -*-

import pymysql
import re
import jieba
import pickle
import os

# 从数据库中返回数据，以map的形式返回 {id:doccontent}
def selectall(table='news_content', host='localhost',user='root',passwd='root',db='IR',charset='utf8',port = 3306):
    docs = {}
    # 含泪记录: 这里的charset是utf8而不是utf-8
    if host == 'localhost' or host =='127.0.0.1':
        mdb = pymysql.connect(host=host,user=user,passwd=passwd,db=db,charset=charset)
    else:
        mdb = pymysql.connect(host=host,port = port,user=user,passwd=passwd,db=db,charset=charset)
    cursor = mdb.cursor()
    cursor.execute('SELECT id, content FROM %s' %table)
    try:
        results = cursor.fetchall() 
        for row in results:
            docid = row[0]
            doccon = row[1]
            docs[docid] = doccon
    except:
        s = 'Error:unable to fetch data'
        print (s)
    mdb.close()
    return docs

# 从数据库中指定id的数据，以map的形式返回
def selectbyid(table='news_content',host='localhost',user='root',passwd='root',db='IR',charset='utf8',port=3306,ids=''):
    docs = []
    # 含泪记录: 这里的charset是utf8而不是utf-8
    if host == 'localhost' or host =='127.0.0.1':
        mdb = pymysql.connect(host=host,user=user,passwd=passwd,db=db,charset=charset)
    else:
        mdb = pymysql.connect(host=host,port = port,user=user,passwd=passwd,db=db,charset=charset)
    cursor = mdb.cursor()
    for id in ids:
        sql = " SELECT paper_url, title, snippet, create_time, hot, content FROM %s WHERE id=%d "%(table,id)
        cursor.execute(sql)
        try:
            results = cursor.fetchall() 
            for row in results:
                tmp = {}
                tmp['url'] = row[0]
                tmp['title'] = row[1]
                tmp['snippet'] = row[2]
                tmp['create_time'] = row[3]
                tmp['hot'] = row[4]
                tmp['content'] = row[5]
                docs.append(tmp)
                break
        except:
            s = 'Error:unable to fetch data'
            print (s)
    mdb.close()
    return docs

# 清洗数据，去掉标点符号，英文字符等等
def clean(docs):
    for key,val in docs.items():
        docs[key] = re.sub("[\s+\.\!\/_,\?:;$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）：＂；]+|[\d]+|[A-Za-z]", "", val)
    return docs

# 分词
def segment(docs):
    # docs = clean(docs)
    i = 1
    for key,val in docs.items():
        print('doc: ', i)
        i += 1
        docs[key] = list(jieba.cut(val, cut_all=False))
    return docs  # 长这个样子的{id:[word, word], id:[word, word]}


# 过滤停用词
def stopwords(docs):
    if os.path.isfile('stop_words_list.pkl'):
        with open('stop_words_list.pkl', 'r') as f:
            stop_words_list = pickle.load(f)
    else:
        path = 'stop_words.txt'
        stop_words_list = []
        with open(path, 'r') as f:
            fobj = f.readlines()
            for line in fobj:
                stop_words_list.append(line.replace('\n','').strip())
    i=1
    for docid,words in docs.items():
        print('doc: ', i)
        i+=1
        new_words = []
        for word in words:
            if word not in stop_words_list:
                new_words.append(word)
            else:
                print (word)
        docs[docid] = new_words
    # 保存过滤停用词之后的文档信息
    with open('docs.pkl', 'wb') as f:
        pickle.dump(docs, f)
    return docs    

# 计算文档长度和平均文档长度
def cal_doc_len(docs):
    docs_dict = {}
    num = 0.0
    total = 0.0
    for key,val in docs.items():
        docs_dict[key] = float(len(val))
        num+=1
        total+=float(len(val))
    docs_dict['davg'] = total/num
    with open('dlenmap.pkl', 'wb') as f:
        pickle.dump(docs_dict, f)

# 生成title和id对应的map
def titleandid():
    titlefile = {}
    titles = []
    title_id = []
    with open('title.txt', 'r') as f:
        fobj = f.readlines()
        for line in fobj:
            titles.append(line.strip('\n').split())
    with open('title_id.txt', 'r') as f:
        fobj = f.readlines()
        for line in fobj:
            title_id.append(int(line.strip('\n')))
    for i in range(len(title_id)):
        titlefile[title_id[i]] = titles[i]
    with open('titleandid.pkl', 'wb') as f:
        pickle.dump(titlefile, f)

if __name__ == '__main__':
    # id = 'D4JELLUF000187VE'
    # selectbyid(id=id)
    # docs = selectall()
    # docs = clean(docs)
    # docs = segment(docs)
    # docs = stopwords(docs)

    with open('docs.pkl', 'rb') as f:
        docs = pickle.load(f)
    cal_doc_len(docs)    
    