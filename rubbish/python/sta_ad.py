# -*- coding: utf-8 -*-

import os
import scws
import csv
import re
from svmutil import *

SCWS_ENCODING = 'utf-8'
SCWS_RULES = '/usr/local/scws/etc/rules.utf8.ini'
CHS_DICT_PATH = '/usr/local/scws/etc/dict.utf8.xdb'
CHT_DICT_PATH = '/usr/local/scws/etc/dict_cht.utf8.xdb'
IGNORE_PUNCTUATION = 1

ABSOLUTE_DICT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), './dict'))
CUSTOM_DICT_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'userdic.txt')
EXTRA_STOPWORD_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'stopword.txt')
EXTRA_EMOTIONWORD_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'emotionlist.txt')
EXTRA_ONE_WORD_WHITE_LIST_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'one_word_white_list.txt')
EXTRA_BLACK_LIST_PATH = os.path.join(ABSOLUTE_DICT_PATH, 'black.txt')

def load_scws():
    s = scws.Scws()
    s.set_charset(SCWS_ENCODING)

    s.set_dict(CHS_DICT_PATH, scws.XDICT_MEM)
    s.add_dict(CHT_DICT_PATH, scws.XDICT_MEM)
    s.add_dict(CUSTOM_DICT_PATH, scws.XDICT_TXT)

    # 把停用词全部拆成单字，再过滤掉单字，以达到去除停用词的目的
    s.add_dict(EXTRA_STOPWORD_PATH, scws.XDICT_TXT)
    # 即基于表情表对表情进行分词，必要的时候在返回结果处或后剔除
    s.add_dict(EXTRA_EMOTIONWORD_PATH, scws.XDICT_TXT)

    s.set_rules(SCWS_RULES)
    s.set_ignore(IGNORE_PUNCTUATION)
    return s

def cut_filter(text):
    pattern_list = [r'\（分享自 .*\）', r'http://\w*']
    for i in pattern_list:
        p = re.compile(i)
        text = p.sub('', text)
    return text

def test(texts,flag):
    word_dict = dict()
    reader = csv.reader(file('./svm/feature20150124.csv', 'rb'))
    for w,c in reader:
        word_dict[str(w)] = c 

    sw = load_scws()
    items = []
    for text in texts:
        words = sw.participle(text)
        row = dict()
        for word in words:
            if row.has_key(str(word[0])):
                row[str(word[0])] = row[str(word[0])] + 1
            else:
                row[str(word[0])] = 1
        items.append(row)


    f_items = []
    for i in range(0,len(items)):
        row = items[i]
        f_row = ''
        f_row = f_row + str(1)
        for k,v in word_dict.iteritems():
            if row.has_key(k):
                item = str(word_dict[k])+':'+str(row[k])
                f_row = f_row + ' ' + str(item) 
        f_items.append(f_row)

    with open('./svm_test/test%s.txt' % flag, 'wb') as f:
        writer = csv.writer(f)
        for i in range(0,len(f_items)):
            row = []
            row.append(f_items[i])
            writer.writerow((row))
    f.close()
    return items
    
def choose_ad(flag):
##    y, x = svm_read_problem('./svm/train20150124.txt')
##    m = svm_train(y, x, '-c 4 -h 0')
##    svm_save_model('./svm/train.model',m)
    m = svm_load_model('./svm/train.model')
    y, x = svm_read_problem('./svm_test/test%s.txt' % flag)
    p_label, p_acc, p_val  = svm_predict(y, x, m)

    return p_label

def start_ad(weibo,flag):
    '''
    垃圾过滤主函数：
    输入数据:weibo(list元素)，示例：[[mid,text,...],[mid,text,...]...]
            flag(标记变量，任意设置)
    输出数据:label_data(字典元素)，示例：{{'mid':类别标签},{'mid':类别标签}...}
            1表示垃圾文本，0表示非垃圾文本
    '''
    weibo_mid = []
    texts = []
    label_data = dict()#标签字典，0表示非垃圾文本，1表示垃圾文本
    for i in range(0,len(weibo)):
        mid = weibo[i][0]
        text = weibo[i][1]
##        n = str(text).count('@')#去掉多于10个@符号的文本
##        if n >= 10:
##            label_data[str(mid)] = 1
##            continue
##        n = str(text).find('//')#去掉//前文本长度小于10的文本
##        if n >= 0 and n <= 9:
##            label_data[str(mid)] = 1
##            continue
        value = cut_filter(text)
        if len(value) > 0:#去掉只含有字母或空文本
            if text != '转发微博':#去掉仅含有“转发微博”的文本
                weibo_mid.append(str(mid))
                texts.append(text)
                label_data[str(mid)] = 0
            else:
                label_data[str(mid)] = 1
        else:
            label_data[str(mid)] = 1

    if len(weibo_mid) == 0:
        return label_data
    
    test(texts,flag)#生成测试数据
    
    lable = choose_ad(flag)#广告过滤
    print 'len(lable), len(weibo_mid):',len(lable), len(weibo_mid)
    for i in range(0,len(lable)):        
        if lable[i] == 1:
            label_data[str(weibo_mid[i])] = 1

    return label_data
