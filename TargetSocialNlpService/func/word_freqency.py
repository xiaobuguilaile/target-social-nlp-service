# -*-coding:utf-8 -*-

'''
@File       : word_freqency.py
@Author     : HW Shen
@Date       : 2020/9/21
@Desc       :
'''

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
import json
from loguru import logger
import re

from TargetSocialNlpService.utils.RESPONSE import RET
from TargetSocialNlpService.utils.timer import time_count
from TargetSocialNlpService.utils.jieba_speed_up import chinese_word_segment


class GenerateWordFreq(object):
    """ 词云所需词频统计及词云展示 """

    def __init__(self, mode="normal"):

        self.mode = mode
        self.load_data()  # 加载所需数据集
        self.output_dic = {}  # 输出词频结果

    def load_data(self):

        self.stopwords = [line.strip() for line in open(BASE_DIR + "/data/chinese_stopwords.txt", encoding="utf-8").readlines()]

    @time_count
    def get_words_freq(self, text:str):
        """ 词频生成主程序 """

        logger.info(" text length is : {} ".format(len(text)))

        # 构建api接口返回数据
        return_dict = {'status': RET.OK,
                       'response': 'success',
                       'words_freq': {}}

        clean_text = re.findall('[\u4e00-\u9fa5]+', text, re.S)  # 只保留中文，字母，数字，标点
        text = "".join(clean_text)

        # 输入数据为空处理
        if len(text) <= 1:
            return_dict = {'status': RET.NODATA,
                           'response': 'fail',
                           'words_freq': {}}
            return json.dumps(return_dict, ensure_ascii=False)

        jieba_words = [word for word in self.jieba_cut(text) if word not in self.stopwords]  # jieba分词
        self.count_dict = Counter(jieba_words)  # 词频统计
        print("count_dict", self.count_dict)

        return_dict["words_freq"] = self.count_dict

        return json.dumps(return_dict, ensure_ascii=False)

    def jieba_cut(self, text):

        return chinese_word_segment(text)


if __name__ == '__main__':

    import pandas as pd

    df = pd.read_csv(BASE_DIR + "/test/kwaishou_comment.csv")  # 读取源数据，将数据解析为时间格式
    df = df.drop_duplicates()  # 去重
    print("Remove duplicate items completed! ")
    df = df.dropna(subset=["评论内容"])  # 删除 “评论内容” 空值行

    text = " ".join(list(df["评论内容"]))

    g = GenerateWordFreq()
    g.get_words_freq(text)
