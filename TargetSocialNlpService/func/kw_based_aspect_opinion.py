# -*-coding:utf-8 -*-

'''
@File       : kw_based_aspect_opinion.py
@Author     : HW Shen
@Date       : 2020/9/16
@Desc       :
'''

import re
from TargetSocialNlpService.utils.RESPONSE import RET
import json
import jieba_fast as jieba
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_BASE = BASE_DIR + "/data/"
SPECIAL_WORDS = [line.strip() for line in open(DATA_BASE + "kwords.txt", encoding="utf-8").readlines()]
# print(SPECIAL_WORDS)

# 对特殊词组作 "不拆分" 限定
for w in SPECIAL_WORDS:
    jieba.suggest_freq(w, tune=True)

from aip import AipNlp
# 利用百度云提供的API接口实现情感分析
APP_ID = '22678530'
API_KEY = 'C7ZItdUG22PKLpqBDrSO4xZn'
SECRET_KEY = 'N3CIe75AHiMSaIjWzoIfFK1tegYkmYCZ'
client = AipNlp(APP_ID, API_KEY, SECRET_KEY)


class KeywordsBasedAspectOpinion(object):

    def __init__(self):

        self.output = {}
        self.jieba_words = []
        self.split_texts = []
        self.load_data()
        # 中兴评论标定词
        self.normal_judge_words = ["刚收到货", "用了之后给评价", "还没有使用", "还没试",  "用后评价", "还没使用",
            "还没开始用", "试过后再评", "还没用", "还没有用", "用完再说", "用了再来追评", "还未使用",
            "用了再来评价", "收到还没用", "用了再说", "还没有试", "过几天试试"]

        # 只到 L1级 分类
        self.L1_only_list = ["L1_快递包装", "L1_客服", "L1_正品", "L1_物流"]
        # 只到 L2级 分类
        self.L1_L2_map = {"L1_产品力": ["L2_产品通用效果", "L2_味道", "L2_成分"],
                          "L1_产品包装": ["L2_外包装", "L2_产品设计", "L2_容量"],
                          "L1_价格": ["L2_定价", "L2_促销", "L2_礼物"]
        }
        # 下沉到 L3级 分类
        self.L2_L3_map = {"L2_功效": ["L3_保湿滋润", "L3_养肤", "L3_温和", "L3_提亮&美白", "L3_防晒", "L3_控油", "L3_遮瑕", "L3_持久"],
                          "L2_质地&肤感": ["L3_轻薄", "L3_细腻", "L3_水润", "L3_粘腻", "L3_好推开", "L3_服帖", "L3_通用质地"],
                          "L2_颜色&色号": ["L3_修正肤色", "L3_色号"],
                          "L2_肤质": ["L3_干皮", "L3_油皮"],
                          "L2_妆效": ["L3_混合肌", "L3_中性肌", "L3_敏感肌", "L3_痘肌", "L3_哑光肌", "L3_奶油肌", "L3_自然", "L3_裸妆", "L3_丝绸", "L3_水光肌", "L3_光泽肌", "L3_瓷肌", "L3_空气感"]
        }
        self.L2_L1_map = {"L2_产品通用效果": "L1_产品力",
                          "L2_味道": "L1_产品力",
                          "L2_成分": "L1_产品力",
                          "L2_功效": "L1_产品力",
                          "L2_质地&肤感": "L1_产品力",
                          "L2_颜色&色号": "L1_产品力",
                          "L2_肤质": "L1_产品力",
                          "L2_妆效": "L1_产品力",
                          "L2_外包装": "L1_产品包装",
                          "L2_产品设计": "L1_产品包装",
                          "L2_定价": "L1_价格",
                          "L2_促销": "L1_价格",
                          "L2_礼物": "L1_价格"}

    def load_data(self):

        self.base = json.loads(open(DATA_BASE + "EC_output_structure_new.json", encoding="utf-8").read())
        self.output = json.loads(open(DATA_BASE + "structure.json", encoding="utf-8").read())
        # print(self.output)

    def get_baidu_sentiment(self, input_text):

        for word in self.normal_judge_words:
            if word in input_text:
                return 0
        try:
            # 利用 baidu 的 api 接口获取情感分析结果
            result = client.sentimentClassify(input_text)
            print("baidu result: ", result)
            items = result["items"][0]
        except Exception as e:
            import time
            time.sleep(2)
            print("百度api接口访问超出限制：", e)
            # 利用 Baidu 的 api 接口获取情感分析结果
            result = client.sentimentClassify(input_text)
            print("baidu result: ", result)
            items = result["items"][0]

        emotion = 1 if items["positive_prob"] > 0.5 else -1

        return emotion
    
    def get_splited_sentiment(self, keyword):
        """ 找到当前关键词所处的片段，及其情感 """
        
        for split_text in self.split_texts:
            if keyword in split_text:
                emotion = self.get_baidu_sentiment(split_text)
                print(keyword, ": ", split_text, ": ", emotion)
                return emotion

    def get_segment(self, review_text, aspect):
        """ 通过标点符号和转折词对 text进行切分，获取某个 aspect 的短句 """

        # if self.is_review_only_one_aspect(review_text):
        #     return review_text

        cur_aspect_index = review_text.index(aspect)
        cur_aspect_end_index_begin = cur_aspect_index + len(aspect)  # aspect开始的下标
        cur_aspect_end_index_end = cur_aspect_end_index_begin  # aspect结束的下标
        end_pos = len(review_text) - 1

        stop_punct_map = {c: None for c in '，。！？； '}  # 标点符号
        # stop_punct_map = {c: None for c in ',.!?;'}  # 标点符号
        # relation_punct_list = ["and", "when", "but"]  # 转折词

        # next_aspect = self.get_next_aspect(review_text[cur_aspect_end_index_begin:end_pos])
        # 从 “aspect开始的下标” 到 “text结束” 的部分查找 “形容词 adj”
        # cur_aspect_des = self.get_cur_aspect_adj(review_text[cur_aspect_end_index_begin:end_pos])

        while cur_aspect_end_index_end <= end_pos:

            # 在 “标点符号” 处截取
            cur_str = review_text[cur_aspect_end_index_end:min(cur_aspect_end_index_end + 1, end_pos)]
            if cur_str in stop_punct_map:
                break

            cur_aspect_end_index_end += 1

        cur_aspect_end_index_end = min(cur_aspect_end_index_end, end_pos)
        return review_text[cur_aspect_index:cur_aspect_end_index_end]

    def get_output(self, input_text):

        # 构建api接口返回数据
        return_dict = {'status': RET.OK,
                       'response': 'success',
                       'sentiment_res': {}}

        self.output["text"] = input_text
        self.jieba_words = jieba.lcut(input_text.replace("：", ""))  # 获得 jieba 切词结果
        print("jieba_words: ", self.jieba_words)
        self.split_texts = re.split('[，。？,.;?: ]+', input_text.strip())
        print("split_texts: ", self.split_texts)
        emotion = self.get_baidu_sentiment(input_text)  # 百度api给出整体评价
        self.output["res"]["emotion"] = emotion

        self.get_general_comment(input_text)  # 获得 general 总评

        self.get_only_l1_comment()
        self.get_l1_l2_comment()
        self.get_11_l2_l3_comment()

        print(self.output)

        return_dict["sentiment_res"] = self.output

        return json.dumps(return_dict, ensure_ascii=False)

    def get_general_comment(self, text):
        """ 匹配 general评论信息，并把结果加入 ouput """

        for word in self.jieba_words:
            if word in SPECIAL_WORDS:
                return
        if len(text) <= 5:  # 总评长度限制

            for g_word in self.base["通用评论"]["good"]:
                if g_word in text:
                    # self.output["res"]["emotion"] = 1
                    self.output["details"]["通用评论"]["match"].append(g_word)
                    self.output["details"]["通用评论"]["emotion"] = 1
                    return

            for n_word in self.base["通用评论"]["normal"]:
                if n_word in text:
                    # self.output["res"]["emotion"] = 0
                    self.output["details"]["通用评论"]["match"].append(n_word)
                    self.output["details"]["通用评论"]["emotion"] = 0
                    return

            for b_word in self.base["通用评论"]["bad"]:
                if b_word in text:
                    # self.output["res"]["emotion"] = -1
                    self.output["details"]["通用评论"]["match"].append(b_word)
                    self.output["details"]["通用评论"]["emotion"] = -1
                    return

    def get_only_l1_comment(self):
        """ 匹配 L1 的评论信息，并把结果加入 output """

        # Only_L1_level
        for L1_keyword in self.L1_only_list:
            for g_word in self.base[L1_keyword]["good"]:
                if g_word in self.jieba_words:
                    splited_emotion = self.get_splited_sentiment(g_word)
                    self.output["res"]["matched_emotion"].append({
                        "match_item": L1_keyword,
                        "emotion": splited_emotion,
                        "level_path":[L1_keyword]
                    })
                    self.output["details"][L1_keyword]["match"].append(g_word)
                    self.output["details"][L1_keyword]["emotion"] = 1
                    break
            for n_word in self.base[L1_keyword]["normal"]:
                if n_word in self.jieba_words:
                    splited_emotion = self.get_splited_sentiment(n_word)
                    self.output["res"]["matched_emotion"].append({
                        "match_item": L1_keyword,
                        "emotion": splited_emotion,
                        "level_path": [L1_keyword]
                    })
                    self.output["details"][L1_keyword]["match"].append(n_word)
                    self.output["details"][L1_keyword]["emotion"] = 0
                    break
            for b_word in self.base[L1_keyword]["bad"]:
                if b_word in self.jieba_words:
                    splited_emotion = self.get_splited_sentiment(b_word)
                    self.output["res"]["matched_emotion"].append({
                        "match_item": L1_keyword,
                        "emotion": splited_emotion,
                        "level_path": [L1_keyword]
                    })
                    self.output["details"][L1_keyword]["match"].append(b_word)
                    self.output["details"][L1_keyword]["emotion"] = -1
                    break

    def get_l1_l2_comment(self):

        # L1_L2_level
        for L1_keyword in self.L1_L2_map:
            for L2_keyword in self.L1_L2_map[L1_keyword]:
                # print(L2_keyword)
                for g_word in self.base[L1_keyword][L2_keyword]["good"]:
                    if g_word in self.jieba_words:
                        splited_emotion = self.get_splited_sentiment(g_word)
                        self.output["res"]["matched_emotion"].append({
                            "match_item": L2_keyword,
                            "emotion": splited_emotion,
                            "level_path": [L2_keyword, L1_keyword]
                        })
                        self.output["details"][L1_keyword][L2_keyword]["match"].append(g_word)
                        self.output["details"][L1_keyword][L2_keyword]["emotion"] = 1
                        self.output["details"][L1_keyword]["emotion"] += 1
                        break
                for n_word in self.base[L1_keyword][L2_keyword]["normal"]:
                    if n_word in self.jieba_words:
                        splited_emotion = self.get_splited_sentiment(n_word)
                        self.output["res"]["matched_emotion"].append({
                            "match_item": L2_keyword,
                            "emotion": splited_emotion,
                            "level_path": [L2_keyword, L1_keyword]
                        })
                        self.output["details"][L1_keyword][L2_keyword]["match"].append(n_word)
                        self.output["details"][L1_keyword][L2_keyword]["emotion"] = 0
                        break
                for b_word in self.base[L1_keyword][L2_keyword]["bad"]:
                    if b_word in self.jieba_words:
                        splited_emotion = self.get_splited_sentiment(b_word)
                        self.output["res"]["matched_emotion"].append({
                            "match_item": L2_keyword,
                            "emotion": splited_emotion,
                            "level_path": [L2_keyword, L1_keyword]
                        })
                        self.output["details"][L1_keyword][L2_keyword]["match"].append(b_word)
                        self.output["details"][L1_keyword][L2_keyword]["emotion"] = -1
                        self.output["details"][L1_keyword]["emotion"] -= 1
                        break

    def get_11_l2_l3_comment(self):

        # L1_L2_L3_level
        for L2_keyword in self.L2_L3_map:
            L1_keyword = self.L2_L1_map[L2_keyword]
            for L3_keyword in self.L2_L3_map[L2_keyword]:
                for g_word in self.base["L1_产品力"][L2_keyword][L3_keyword]["good"]:
                    if g_word in self.jieba_words:
                        splited_emotion = self.get_splited_sentiment(g_word)
                        self.output["res"]["matched_emotion"].append({
                            "match_item": L3_keyword,
                            "emotion": splited_emotion,
                            "level_path": [L3_keyword, L2_keyword, L1_keyword]
                        })
                        self.output["details"]["L1_产品力"][L2_keyword][L3_keyword]["match"].append(g_word)
                        self.output["details"]["L1_产品力"][L2_keyword][L3_keyword]["emotion"] = 1
                        self.output["details"]["L1_产品力"][L2_keyword]["emotion"] += 1
                        self.output["details"]["L1_产品力"]["emotion"] += 1
                        break
                for n_word in self.base["L1_产品力"][L2_keyword][L3_keyword]["normal"]:
                    if n_word in self.jieba_words:
                        splited_emotion = self.get_splited_sentiment(n_word)
                        self.output["res"]["matched_emotion"].append({
                            "match_item": L3_keyword,
                            "emotion": splited_emotion,
                            "level_path": [L3_keyword, L2_keyword, L1_keyword]
                        })
                        self.output["details"]["L1_产品力"][L2_keyword][L3_keyword]["match"].append(n_word)
                        self.output["details"]["L1_产品力"][L2_keyword][L3_keyword]["emotion"] = 0
                        break
                for b_word in self.base["L1_产品力"][L2_keyword][L3_keyword]["bad"]:
                    if b_word in self.jieba_words:
                        splited_emotion = self.get_splited_sentiment(b_word)
                        self.output["res"]["matched_emotion"].append({
                            "match_item": L3_keyword,
                            "emotion": splited_emotion,
                            "level_path": [L3_keyword, L2_keyword, L1_keyword]
                        })
                        self.output["details"]["L1_产品力"][L2_keyword][L3_keyword]["match"].append(b_word)
                        self.output["details"]["L1_产品力"][L2_keyword][L3_keyword]["emotion"] = -1
                        self.output["details"]["L1_产品力"][L2_keyword]["emotion"] -= 1
                        self.output["details"]["L1_产品力"]["emotion"] -= 1
                        break


if __name__ == '__main__':

    # input_text = "保湿控油很差，一下就油了，而且浮粉很严重，最难用的粉底液，（我是不容易脱妆的肌肤）无关黑他，如实告知自己使用效果，唉"
    input_text = "很快很好，不愧是大牌"
    # print(re.split('[，。？ ,.?]+', input_text.strip()))

    ob = KeywordsBasedAspectOpinion()
    ob.get_output(input_text)
    # seg_txt = ob.get_segment(input_text, "浮粉")
    # print(seg_txt)

    # ob.get_baidu_sentiment(input_text)
    # import requests
    # API_key = 'C7ZItdUG22PKLpqBDrSO4xZn'
    # secret_key = 'N3CIe75AHiMSaIjWzoIfFK1tegYkmYCZ'
    # host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}'.format(
    #     API_key, secret_key)
    # res = requests.post(host)
    # print(res.text)

    # result = client.sentimentClassify(input_text)
    # print(result)

