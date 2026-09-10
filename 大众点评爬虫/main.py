# -*- coding: utf-8 -*-
"""
Created on Mon Jul  9 16:42:52 2018

@author: bin
"""

#目标爬取店铺的评论

import requests
from bs4 import BeautifulSoup
import time, random
import mysqls
import re
from fake_useragent import UserAgent
import os
import json

ua = UserAgent()

#设置cookies
cookie = os.environ.get("DIANPING_COOKIE", "")

#修改请求头
headers = {
        'User-Agent':ua.random,
        'Cookie':cookie,
        'Connection':'keep-alive',
        'Host':'www.dianping.com',
        'Referer': 'http://www.dianping.com/shop/521698/review_all/p6'
}

#从ip代理池中随机获取ip
#ips = open('proxies.txt','r').read().split('\n')
#
#def get_random_ip():
#    ip = random.choice(ips)
#    pxs = {ip.split(':')[0]:ip}
#    return pxs

#获取html页面
def getHTMLText(url,code="utf-8"):
    try:
        time.sleep(random.random()*6 + 2)
        r=requests.get(url, timeout = 5, headers=headers, 
#                       proxies=get_random_ip()
                       )
        r.raise_for_status()
        r.encoding = code
        return r.text
    except Exception as e:
        print(f"产生异常: {e}")
        return "产生异常"

#因为评论中带有emoji表情，是4个字符长度的，mysql数据库不支持4个字符长度，因此要进行过滤
def remove_emoji(text):
    try:
        highpoints = re.compile(u'[\U00010000-\U0010ffff]')
    except re.error:
        highpoints = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    return highpoints.sub(u'',text)

#从html中提起所需字段信息
def parsePage(html,shpoID):
    infoList = [] #用于存储提取后的信息，列表的每一项都是一个字典
    soup = BeautifulSoup(html, "html.parser")
    
    for item in soup('div','main-review'):
        cus_id = item.find('a','name').text.strip()
        comment_time = item.find('span','time').text.strip()
        try:
            comment_star = item.find('span',re.compile('sml-rank-stars')).get('class')[1]
        except Exception:
            comment_star = 'NAN'
        cus_comment = item.find('div',"review-words").text.strip()
        scores = str(item.find('span','score'))
        try:
            kouwei = re.findall(r'口味：([\u4e00-\u9fa5]*)',scores)[0]
            huanjing = re.findall(r'环境：([\u4e00-\u9fa5]*)',scores)[0]
            fuwu = re.findall(r'服务：([\u4e00-\u9fa5]*)',scores)[0]
        except Exception:
            kouwei = huanjing = fuwu = '无'
        
        infoList.append({'cus_id':cus_id,
                         'comment_time':comment_time,
                         'comment_star':comment_star,
                         'cus_comment':remove_emoji(cus_comment),
                         'kouwei':kouwei,
                         'huanjing':huanjing,
                         'fuwu':fuwu,
                         'shopID':shpoID})
    return infoList

#构造每一页的url，并且对爬取的信息进行存储
def getCommentinfo(shop_url, shpoID, page_begin, page_end):
    for i in range(page_begin, page_end):
        try:
            url = shop_url + 'p' + str(i)
            html = getHTMLText(url)
            infoList = parsePage(html,shpoID)
            print('成功爬取第{}页数据,有评论{}条'.format(i,len(infoList)))
            for info in infoList:
                mysqls.save_data(info)
            #断点续传中的断点
            if (html != "产生异常") and (len(infoList) != 0):
                state = {}
                if os.path.exists('xuchuan.json'):
                    try:
                        with open('xuchuan.json', 'r') as file:
                            state = json.load(file)
                    except json.JSONDecodeError:
                        pass
                state[shpoID] = i
                with open('xuchuan.json', 'w') as file:
                    json.dump(state, file)
            else:
                print('休息60s...')
                time.sleep(60)
        except Exception as e:
            print(f'跳过本次: {e}')
            continue
    return

def xuchuan(shopID):
    if os.path.exists('xuchuan.json'):
        try:
            with open('xuchuan.json', 'r') as file:
                state = json.load(file)
                return state.get(shopID, 0)
        except json.JSONDecodeError:
            pass
    elif os.path.exists('xuchuan.txt'):
        # Fallback to older format, but highly inaccurate for multiple shops
        file = open('xuchuan.txt','r')
        lines = file.readlines()
        file.close()
        if lines:
            return int(lines[-1])
    return 0

#根据店铺id，店铺页码进行爬取
def craw_comment(shopID='521698',page = 53):
    shop_url = "http://www.dianping.com/shop/" + shopID + "/review_all/"
    #读取断点续传中的续传断点
    nowpage = xuchuan(shopID)
    getCommentinfo(shop_url, shopID, page_begin=nowpage+1, page_end=page+1)
    mysqls.close_sql()
    return

if __name__ == "__main__":
    craw_comment()
        