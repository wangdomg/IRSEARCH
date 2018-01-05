# -*- coding:utf-8 -*-
_author_ = 'zoux'
from flask import Flask, render_template, request
import json
import operator
import math
import pickle
from search import getPages
import gensim
app = Flask(__name__)

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
with open('hotnews.pkl', 'rb') as f:
    hotnews = pickle.load(f)
model = gensim.models.Word2Vec.load('word2vec_model')


recent_search = ""
searlist = u'结婚'
recommend_list = [u'恋爱', u'同居', u'再婚']
newslist = [
    {'title': u'【get】111：等政府调查结论，对诬告陷害已报案11',
     'abstract': u'红黄蓝官方微博于今早发声明称，已配合警方提供相关监控资料及设备，涉事老师暂停职，对于个别人士涉嫌诬告、陷害的行为，新天地幼儿园园长已经向公安机关报案。',
     'url': 'https://www.huxiu.com/article/223278.html',
     "add_time": '2017-06-28 12:00:00',
     'furl': 'https://www.huxiu.com/article/223278.html',
     'ftitle': u'等政府调查结论，对诬告陷害已报案',
     "hot": 1,
     'rel': 10.0,
     },

    {'title': u'【get】222：等政府调查结论，对诬告陷害已报案',
     'abstract': u'红黄蓝官方微博于今早发声明称，已配合警方提供相关监控资料及设备，涉事老师暂停职，对于个别人士涉嫌诬告、陷害的行为，新天地幼儿园园长已经向公安机关报案。',
     'url': 'https://www.huxiu.com/article/223278.html',
     "add_time": '2017-06-05 12:00:00',
     'furl': 'https://www.huxiu.com/article/223278.html',
     'ftitle': u'等政府调查结论，对诬告陷害已报案',
     "hot": 5,
     'rel': 9.5
     }
]

def get_page(total,p):
    show_page = 5   # 显示的页码数
    pageoffset = 2  # 偏移量
    start = 1    #分页条开始
    end = total  #分页条结束

    if total > show_page:
        if p > pageoffset:
            start = p - pageoffset
            if total > p + pageoffset:
                end = p + pageoffset
            else:
                end = total
        else:
            start = 1
            if total > show_page:
                end = show_page
            else:
                end = total
        if p + pageoffset > total:
            start = start - (p + pageoffset - end)
    #用于模版中循环
    dic = range(start, end + 1)
    return dic

def ReadJson(filename):
    with open('./'+filename, 'r') as f:
        json_dict = json.load(f)
        return json_dict['result']

#得到当前页的内容,总记录条数
def get_NewsList(content_list,page_limit,p):
    count = len(content_list)
    result = content_list[(p-1)*page_limit:p*page_limit]
    return result,count

#搜索首页
@app.route('/index',methods=['POST','GET'])
def index():
    global hotnews
    return render_template("test.html", hotnews_dic=hotnews[0:30])

#get方法
@app.route('/search',methods=['GET'])
def search_get():
    search_word = request.args.get('searchword')
    sorted_value = request.args.get('sorted')
    if(sorted_value==None):
        sorted_value = 'fsim'
    global recent_search
    global recommend_list
    global newslist
    global searlist
    global fenci 
    print ('recent_search',recent_search)
    print ('search_word',search_word)
    if(recent_search==search_word and search_word!=''):
        pass
    elif search_word!='':
        res = getPages(search_word, tfmap, idfmap, trie, titleandid, model, dlenmap)
        newslist = res['pages']
        recommend_list = res['words']
        fenci = res['fenci']
    else:
        searlist = []
        recommend_list = []
        newslist = []
    sortNewsList = sort_news(sorted_value, newslist)


    p = request.args.get("p", '')  # 页数
    show_shouye_status = 0  # 显示首页状态
    page_limit = 5  # 每页显示1条数据
    if p == '':
        p = 1
    else:
        p = int(p)
        if p > 1:
            show_shouye_status = 1
    news_list, count = get_NewsList(sortNewsList,page_limit, p)  # 得到当前页的内容,总记录条数
    total = int(math.ceil(count / page_limit))  # 总页数

    dic = get_page(total, p)
    datas = {
        'news_list': news_list,
        'recommend_list': recommend_list,
        'search_word': search_word,
        'p': int(p),
        'total': total,
        'show_shouye_status': show_shouye_status,
        'dic_list': dic
    }
    recent_search = search_word
    # return render_template('template_index.html', searlist=searlist, recommend_list=recommend_list, newslist=sortNewsList,searchword=search_word)
    return render_template('c_index.html', datas=datas, fenci=fenci)

import datetime
import operator

def cmp_time(a):
    #a_datatime = datetime.strptime(a['add_time'], '%Y-%m-%d %H:%M:%S').strftime("(%d-%b-%Y)")
    a_datatime = datetime.datetime.strptime(a['fcreate_time'],'%Y-%m-%d %H:%M:%S')
    return a_datatime


def sort_news(sort_key,newslist):
    if(sort_key=="hot"):
        newslist.sort(key=operator.itemgetter('fhot'), reverse=True)  # 默认为升序， reverse=True为降序
    elif(sort_key=='rel'):
        newslist.sort(key=operator.itemgetter('fsim'), reverse=True)  # 默认为升序， reverse=True为降序
    elif(sort_key=='time'):
        newslist = sorted(newslist, key=cmp_time,reverse=True)
    return newslist



#点击进入新闻内容
@app.route('/news')
def newsfunc():
    news_id = request.args.get('id')
    news = {
        "title":"标题",
        "time":"时间",
        'content':"内容",
        'link':'原始链接'
    }
    return render_template('template_news.html',news_id=news_id,news=news)

if __name__ == "__main__":
    app.run(debug=True)

