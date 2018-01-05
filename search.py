#!Python3
# -*- coding:utf-8 -*-

import re
import jieba
import numpy as np
from utils import selectbyid
import pickle
import time
import gensim
from Trie import Trie
from searchrelated import searchrelatedH, searchrelatedB

# 对查询进行预处理
# 输入: string
# 输出: {word:frequency}
def prequery(query):
    query = re.sub("[\.\!\/_,\?:;$%^*(+\"\']+|[+——！，。？、~@#￥%……&*（）：＂；]+|[\d]+|[A-Za-z]", "", query)
    query = query.split()
    word_list = []
    for item in query:
        tmp = list(jieba.cut(item, cut_all=False))
        word_list.extend(tmp)
    keywords = {}
    for word in word_list:
        if word in keywords:
            keywords[word] += 1
        else:
            keywords[word] = 1
    return keywords


# 计算文档的tf值
# 输入: {word:frequency} {word:{docid:tf}} {word:idf}
# 输出: {id:{word:tfidf}}
def doctf(keywords, tfmap):
    dtf = {}
    # 查找tf值
    for word in keywords:
        if word in tfmap:  # 检查这个词是否在tfmap中出现
            docs = tfmap[word]
            for docid in docs:
                if docid in dtf:
                    dtf[docid][word] = docs[docid]*1.0  # 得到在这个文档中这个词的tf值
                else:
                    dtf[docid] = {}
                    dtf[docid][word] = docs[docid]*1.0
    return dtf

# 普通检索
def getPages_normal(query, tfmap, idfmap, dlenmap):
    num = 100

    keywords = prequery(query)
    dtf = doctf(keywords, tfmap)

    # 计算bm25值
    k1=1.2; b=0.75
    docs = {}
    for docid,worddict in dtf.items():
        docs[docid] = 0.0
        for word in keywords:
            if word in worddict:
                docs[docid] += idfmap[word]*( (k1+1)*worddict[word]/( k1*((1-b)+b*dlenmap[docid]/dlenmap['davg'])+worddict[word] ) )

    # 选择余弦相似度最高的几个id
    score_dict = {}  # 每一个网页的余弦相似度打分
    id_score = sorted(docs.items(), key=lambda d:d[1], reverse=True)
    id_list = []  # 每一个网页的id
    for i in range(min(num,len(id_score))):
        id_list.append(id_score[i][0])
        score_dict[id_score[i][0]] = id_score[i][1]
    
    return (id_list, score_dict)  # 返回网页的id和网页的相关度
    

# 通配符检索 
def getPages_general(query, tfmap, idfmap, trie):
    if query.index('*') == 0:
        keywords = trie.search(query[1:]+'$')
    elif query.index('*') == len(query)-1:
        keywords = trie.search('$'+query[:-1])
    else:
        mid = query.index('*')
        keyword = trie.search(query[mid+1:]+'$'+query[:mid])

    res = []
    now = time.time()
    for keyword in keywords:
        if keyword in tfmap:
            for doc in tfmap[keyword]:
                res.append((doc,tfmap[keyword][doc]))
    res = sorted(res,key=lambda x:x[1],reverse=True)
    sum_=0.0
    for t in res:
        sum_+=t[1]**2
    sum_= np.sqrt(sum_)
    print(time.time()-now)
    ids_=[]
    scores=[]
    for t in res:
        ids_.append(t[0])
        scores.append([t[1]]/sum_)
    
    return (ids_[0:100],scores[0:100])


# 检索网页
# 输入: {word:frequency}
# 输出: [{'url':url, 'title':title, 'snippet':snippet}]
def getPages(query, tfmap, idfmap, trie, titleandid, model, dlenmap):
    if '*' in query:
        (id_list, score_dict) = getPages_general(query, tfmap, idfmap, trie)
    else:
        (id_list, score_dict) = getPages_normal(query, tfmap, idfmap, dlenmap)
    
    # 在线进行聚类

    # 过滤掉标题相同的新闻
    newstitle = set()
    uniq_id_list = []
    for id in id_list:
        if ''.join(titleandid[id]) in newstitle:
            continue
        else:
            uniq_id_list.append(id)
            newstitle.add(''.join(titleandid[id]))

    # 构造词向量矩阵，计算标题之间的相似度
    mat = np.zeros([len(uniq_id_list), 200])
    for i in range(len(uniq_id_list)):
        for word in titleandid[uniq_id_list[i]]:
            if word in model:
                mat[i] = mat[i] + model[word]
        # 标准化向量
        down = np.sqrt(mat[i].dot(mat[i]))
        if down != 0.0:
            mat[i] = mat[i]/down
        else:
            mat[i] = mat[i]


    # 计算两两title之间的相似度
    title_sim = {}
    t = 0
    for i in range(len(mat)):
        title_sim[uniq_id_list[i]] = []
        res = mat.dot(mat[i])
        res = zip(uniq_id_list, res)
        r = sorted(res, key=lambda x: x[1], reverse=True)
        r = [v[0] for v in r[0:10]]
        for j in range(len(r)):
            if len(title_sim[uniq_id_list[i]]) >= 2:
                break
            if r[j] != uniq_id_list[i]:  # 除去自身
                title_sim[uniq_id_list[i]].append(r[j])

    # 根据相似度构造查询的id_list
    newsid = set()
    ids = []
    scores = []
    for id in uniq_id_list:
        if id in newsid:
            continue
        else:
            ids.append(id)
            scores.append(score_dict[id])  # 主新闻的相似度打分
            ids.append(title_sim[id][0])
            scores.append(score_dict[id])
            ids.append(title_sim[id][1])
            scores.append(score_dict[id])
            newsid.add(id)
            newsid.add(title_sim[id][0])
            newsid.add(title_sim[id][1])

    # 根据id检索新闻
    pages = selectbyid(table='news_content',ids=ids)

    # 进行相似结果聚类
    res =  {}
    page_list = []
    for i in range(0,len(pages),3):  # 每一条新闻有两条相似新闻
        tmp = {}
        tmp['furl'] = pages[i]['url']
        tmp['ftitle'] = pages[i]['title']
        tmp['fsnippet'] = pages[i]['snippet']
        tmp['fcreate_time'] = pages[i]['create_time']  # 这是string类型，可以直接比较大小
        tmp['fhot'] = pages[i]['hot']  # 这是float类型，可以直接比较大小
        tmp['fcontent'] = pages[i]['content']
        tmp['fsim'] = scores[i]

        tmp['surl'] = pages[i+1]['url']
        tmp['stitle'] = pages[i+1]['title']

        tmp['turl'] = pages[i+2]['url']
        tmp['ttitle'] = pages[i+2]['title']

        page_list.append(tmp)
    
    # 相关查询
    word_list = []
    # word_list = searchrelatedB(query)
    word_list = searchrelatedH(prequery(query), idfmap, model)

    # 获取分词之后的字符串
    words_dict = prequery(query)
    words_str = ' '.join(words_dict.keys())
    print(words_str)
    
    res['pages'] = page_list; res['words'] = word_list; res['fenci'] = words_str
    
    return res

if __name__ == '__main__':
    # 读取索引
    print('读取所有pkl文件')
    with open('tfmap.pkl', 'rb') as f:
        tfmap = pickle.load(f)
    with open('idfmap.pkl', 'rb') as f:
        idfmap = pickle.load(f)
    with open('trie.pkl', 'rb') as f:
        trie = pickle.load(f)
    with open('titleandid.pkl', 'rb') as f:
        titleandid = pickle.load(f)
    with open('dlenmap.pkl', 'rb') as f:
        dlenmap = pickle.load(f)
    model = gensim.models.Word2Vec.load('word2vec_model')
    

    print('开始检索')
    query = '英国将举行脱欧公投 明星发公开信支持＂留欧＂'
    # query = '*国'
    # query = '习近平'
    print(time.time())
    getPages(query, tfmap, idfmap, trie, titleandid, model, dlenmap)
    print(time.time())