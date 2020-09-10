# -*-coding:utf-8 -*-

'''
@File       : word_cloud.py
@Author     : HW Shen
@Date       : 2020/9/9
@Desc       : 词云展示模块
'''


import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(BASE_DIR + "TargetSocialNlpService/")

from TargetSocialNlpService.utils.RESPONSE import RET
import json
import jieba
from collections import Counter
from wordcloud import WordCloud, ImageColorGenerator
import matplotlib.pyplot as plt
import imageio
from loguru import logger
import pandas as pd
import time

logger.info("------------Data Initialization Start--------------")
COMBINED_DIC = json.loads(open(BASE_DIR + "/data/combined_phrases_dict.json", encoding="utf-8").read())
STOPWORDS = [line.strip() for line in open(BASE_DIR + "/data/chinese_stopwords.txt", encoding="utf-8").readlines()]
SPECIAL_WORDS = [line.strip() for line in open(BASE_DIR + "/data/special_phrases.txt", encoding="utf-8").readlines()]
NEG_WORDS = [line.strip() for line in open(BASE_DIR + "/data/neg_phrases.txt", encoding="utf-8").readlines()]
# 对特殊词组作 "不拆分" 限定
for w in SPECIAL_WORDS:
    jieba.suggest_freq(w, tune=True)
logger.info("------------Data Initialization Finish--------------")


class GenerateWordCloud(object):

    """ 词云所需词频统计及词云展示 """

    def __init__(self, mode="normal"):

        self.mode = mode
        self.load_data()  # 加载所需数据集
        self.output_dic = {}  # 输出词频结果
        # self.bg_color = imageio.imread(BASE_DIR + "/libs/earth.jpg")

    def load_data(self):

        # self.combined_dic = json.loads(open(BASE_DIR + "/data/combined_phrases_dict.json", encoding="utf-8").read())
        # self.stopwords = [line.strip() for line in open(BASE_DIR + "/data/chinese_stopwords.txt", encoding="utf-8").readlines()]
        # self.special_words = [line.strip() for line in open(BASE_DIR + "/data/special_phrases.txt", encoding="utf-8").readlines()]
        # # 对特殊词组作 "不拆分" 限定
        # for w in self.special_words:
        #     jieba.suggest_freq(w, tune=True)
        pass

    def get_phrases_freq(self, text:str):
        """ 主程序 """

        logger.info(" text length is : {} ".format(len(text)))

        # 构建api接口返回数据
        return_dict = {'status': RET.OK,
                       'response': 'success',
                       'words_freq': {}}

        # 输入数据为空处理
        if len(text) <= 1:
            return_dict = {'status': RET.NODATA,
                           'response': 'fail',
                           'words_freq': {}}
            return json.dumps(return_dict, ensure_ascii=False)

        t1 = time.time()
        jieba_words = self.jieba_cut(text)  # jieba分词
        t2 = time.time()
        logger.info("jieba cut cost time ： {:.2f} s".format(t2-t1))
        self.count_dict = Counter(jieba_words)  # 词频统计
        t3 = time.time()
        logger.info("words count cost time : {:.2f} s".format(t3-t2))

        filter_special_words = self.filter(jieba_words)  # 清除不符合要求的分词
        t4 = time.time()
        logger.info("words filter cost time : {:.2f} s".format(t4-t3))

        # 通过filter_words对 count_dict 进行过滤
        filter_special_dic = {}
        for w in filter_special_words:
            filter_special_dic[w] = self.count_dict[w]
        # 合并同义词，统一用规定词代替
        self.output_dic = self.combine_synonymy_phrases(filter_special_dic)
        t5 = time.time()
        logger.info("combine synonymy phrases cost : {:.2f} s".format(t5-t4))

        total_phrases_freq = dict(sorted(self.output_dic.items(), key=lambda kv:kv[1], reverse=True))

        neg_phrases_freq = {}
        for phrase, freq in total_phrases_freq.items():
            if phrase in NEG_WORDS:
                neg_phrases_freq[phrase] = total_phrases_freq[phrase]

        return_dict["words_freq"] = total_phrases_freq
        return_dict["neg_words_freq"] = neg_phrases_freq

        logger.info("word cloud total cost : {:.2f} s".format(t5-t1))

        return json.dumps(return_dict, ensure_ascii=False)

    @staticmethod
    def jieba_cut(content):

        jieba_words = jieba.lcut(content)

        return jieba_words

    def filter(self, words):

        # 剔除停止词, 长度=1的词 (eg. "很", "好"), 数字字母词 (eg."59ml")
        # filter_words = [w_f[0] for w_f in self.count_dict.most_common(10000)
        #                 if w_f[0] not in self.stopwords and w_f[0] in self.special_words]
        # filter_words = [w_f[0] for w_f in self.count_dict.most_common(10000) if w_f[0] not in STOPWORDS and w_f[0] in SPECIAL_WORDS]
        filter_words = [w_f[0] for w_f in self.count_dict.most_common(10000) if w_f[0] in SPECIAL_WORDS]

        return filter_words

    def combine_synonymy_phrases(self, filter_dic):
        """ 合并同义词，统一用 >>规定词<< 代替 """

        # total_dic = {**self.combined_dic["pos"], **self.combined_dic["neu"], **self.combined_dic["neg"]}
        total_dic = {**COMBINED_DIC["pos"], **COMBINED_DIC["neu"], **COMBINED_DIC["neg"]}

        output_dic = {}
        # for ph in total_dic:
        #     output_dic[ph] = 0
        for phrase, freq in filter_dic.items():
            flag = False
            for ph, ph_list in total_dic.items():
                if phrase in ph_list:
                    if ph not in output_dic:
                        output_dic[ph] = freq
                    else:
                        output_dic[ph] += freq
                    flag = True
                    break
            if not flag: output_dic[phrase] = freq

        if "好评" in output_dic: del output_dic["好评"]
        if "差评" in output_dic: del output_dic["差评"]
        if "中评" in output_dic: del output_dic["中评"]

        return output_dic

    def build_wc(self, output_file_name):
        """ 构建词云对象 """

        bg_color = imageio.imread(BASE_DIR + "/libs/earth.jpg")  # 获取词云图片背景

        # 设置 WordCloud 对象
        self.wc = WordCloud(background_color='white',  # 背景颜色
                       # mode='RGBA',  # 当参数为“RGBA”并且background_color不为空时，背景为透明
                       prefer_horizontal=1,  # 水平展示词的比例，比如 默认值0.9就是90%水平展示，10%垂直展示
                       max_words=50,  # 最大词数
                       mask=bg_color,  # 设置词云形状为背景图bg_color的尺寸，这里为 999*1000
                       max_font_size=200,  # 显示字体的最大值
                       font_path=BASE_DIR + "/fonts/msyhbd.ttf",  # 指定字体路径
                       color_func=self.set_color_func,  # 设定字体色号
                       # random_state=42,  # 为每个词返回一个PIL颜色，记录此次颜色分配
                       )

        # wc对象的生成器的词频
        self.wc.generate_from_frequencies(self.output_dic)
        image_colors = ImageColorGenerator(bg_color)  # 从图片中取色
        plt.figure()  # 创建画布
        # plt.imshow(self.wc.recolor(color_func=image_colors))  # 绘制图像
        plt.axis("off")  # 关闭坐标轴

        self.wc.to_file(os.path.join(BASE_DIR + "/result/" + output_file_name + "_WC.jpg"))  # 生成词云图片

    @staticmethod
    def set_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        # return "hsl(0, 0%%, %d%%)" % random.randint(60, 100)
        return '#000000'


if __name__ == '__main__':

    output_file_name = "HXZ"
    df = pd.read_csv("../test/" + output_file_name + ".csv")  # 读取源数据
    df = df.fillna(" ")  # 用空格 " "替换 nan
    text = " ".join(list(df["title"])) + " ".join(list(df["content"]))

    gwc = GenerateWordCloud()
    gwc.get_phrases_freq(text)
    gwc.build_wc(output_file_name)

    # print(sys.path)
    # # BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # print(BASE_DIR)
    # print(sys.path)

