#!python3
# -*- coding:utf8 -*-
import requests
import gensim
import pickle

def searchrelatedH(keywords, idfmap, model):
    # 计算查询中每个词的tfidf值，并选出tfidf值最高的那个词
    for k,v in keywords.items():
        if k in idfmap:
            keywords[k] = float(v)*idfmap[k]
        else:
            keywords[k] = float(v)*1.0
    words = sorted(keywords.items(), key=lambda x:x[1], reverse=True)
    keyword = words[0][0]

    # 根据词向量选择最相近的几个词
    relatedwords = model.most_similar([keyword])
    res = []
    for (v1,v2) in relatedwords:
        res.append(v1)
    
    return res

def searchrelatedB(query):
    res = requests.get('http://api.bing.com/osjson.aspx?query='+query).json()[1]
    return res

if __name__ == '__main__':
    model = gensim.models.Word2Vec.load('word2vec_model')
    with open('idfmap.pkl', 'rb') as f:
        idfmap = pickle.load(f)
    keywords = {'英国':1, '脱欧':1}
    print(searchrelatedH(keywords, idfmap, model))