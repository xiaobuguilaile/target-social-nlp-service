# -*-coding:utf-8 -*-

'''
@File       : kw_based_aspect_opinion.py
@Author     : HW Shen
@Date       : 2020/9/16
@Desc       :
'''


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
        self.load_data()
        self.L1_only_list = ["L1_delivery_package", "L1_service", "L1_authenticity", "L1_logistics"]
        self.L1_L2_map = {"L1_product_efficiency":["L2_product_general", "L2_scent", "L2_ingredient"],
                          "L1_product_package":["L2_outer_package", "L2_bottle_package", "L2_volume"],
                          "L1_price":["L2_pricing", "L2_promotion_deals", "L2_gifts"],
        }
        self.L2_L3_map = {"L2_function":["L3_保湿滋润", "L3_养肤", "L3_温和", "L3_提亮&美白", "L3_防晒", "L3_控油", "L3_遮瑕", "L3_持久"],
                          "L2_texture&skin_feel":["L3_轻薄", "L3_细腻", "L3_水润", "L3_粘腻", "L3_好推开", "L3_服帖", "L3_通用质地"],
                          "L2_color&shade":["L3_修正肤色", "L3_色号"],
                          "L2_skin_type":["L3_干皮", "L3_油皮"],
                          "L2_makeup_look":["L3_混合肌", "L3_中性肌", "L3_敏感肌", "L3_痘肌", "L3_哑光肌", "L3_奶油肌", "L3_自然", "L3_裸妆", "L3_丝绸", "L3_水光肌", "L3_光泽肌", "L3_瓷肌", "L3_空气感"]
        }

    def load_data(self):

        self.base = json.loads(open(DATA_BASE + "EC_output_structure_new.json", encoding="utf-8").read())
        self.output = json.loads(open(DATA_BASE + "structure.json", encoding="utf-8").read())
        # print(self.output)

    def get_baidu_sentiment(self, input_text):

        # 利用 Baidu 的 api 接口获取情感分析结果
        result = client.sentimentClassify(input_text)
        # print(result)
        items = result["items"][0]
        emotion = "Positive" if items["positive_prob"] > 0.5 else "Negative"
        # items['sentiment'] = emotion
        # del items["confidence"]
        self.output["sentiment"] = emotion

    def get_segment(self):
        pass

    def get_output(self, input_text):

        # 构建api接口返回数据
        return_dict = {'status': RET.OK,
                       'response': 'success',
                       'sentiment_res': {}}
        self.jieba_words = jieba.lcut(input_text.replace("：", ""))  # 获得 jieba 切词结果
        print(self.jieba_words)

        self.get_baidu_sentiment(input_text)  # 百度api给出整体评价

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

            for g_word in self.base["general"]["good"]:
                if g_word in text:
                    self.output["general"]["match"].append(g_word)
                    self.output["general"]["emotion"] = 1
                    return

            for n_word in self.base["general"]["normal"]:
                if n_word in text:
                    self.output["general"]["match"].append(n_word)
                    self.output["general"]["emotion"] = 0
                    return

            for b_word in self.base["general"]["bad"]:
                if b_word in text:
                    self.output["general"]["match"].append(b_word)
                    self.output["general"]["emotion"] = -1
                    return

    def get_only_l1_comment(self):
        """ 匹配 L1 的评论信息，并把结果加入 ouput """

        # Only_L1_level
        for L1_keyword in self.L1_only_list:
            for g_word in self.base[L1_keyword]["good"]:
                if g_word in self.jieba_words:
                    self.output[L1_keyword]["match"].append(g_word)
                    self.output[L1_keyword]["emotion"] = 1
                    break
            for n_word in self.base[L1_keyword]["normal"]:
                if n_word in self.jieba_words:
                    self.output[L1_keyword]["match"].append(n_word)
                    self.output[L1_keyword]["emotion"] = 0
                    break
            for b_word in self.base[L1_keyword]["bad"]:
                if b_word in self.jieba_words:
                    self.output[L1_keyword]["match"].append(b_word)
                    self.output[L1_keyword]["emotion"] = -1
                    break

    def get_l1_l2_comment(self):

        # L1_L2_level
        for L1_keyword in self.L1_L2_map:
            for L2_keyword in self.L1_L2_map[L1_keyword]:
                # print(L2_keyword)
                for g_word in self.base[L1_keyword][L2_keyword]["good"]:
                    if g_word in self.jieba_words:
                        self.output[L1_keyword][L2_keyword]["match"].append(g_word)
                        self.output[L1_keyword][L2_keyword]["emotion"] = 1
                        self.output[L1_keyword]["emotion"] += 1
                        break
                for n_word in self.base[L1_keyword][L2_keyword]["normal"]:
                    if n_word in self.jieba_words:
                        self.output[L1_keyword][L2_keyword]["match"].append(n_word)
                        self.output[L1_keyword][L2_keyword]["emotion"] = 0
                        break
                for b_word in self.base[L1_keyword][L2_keyword]["bad"]:
                    if b_word in self.jieba_words:
                        self.output[L1_keyword][L2_keyword]["match"].append(b_word)
                        self.output[L1_keyword][L2_keyword]["emotion"] = -1
                        self.output[L1_keyword]["emotion"] -= 1
                        break

    def get_11_l2_l3_comment(self):

        # L1_L2_L3_level
        for L2_keyword in self.L2_L3_map:
            for L3_keyword in self.L2_L3_map[L2_keyword]:
                for g_word in self.base["L1_product_efficiency"][L2_keyword][L3_keyword]["good"]:
                    if g_word in self.jieba_words:
                        self.output["L1_product_efficiency"][L2_keyword][L3_keyword]["match"].append(g_word)
                        self.output["L1_product_efficiency"][L2_keyword][L3_keyword]["emotion"] = 1
                        self.output["L1_product_efficiency"][L2_keyword]["emotion"] += 1
                        self.output["L1_product_efficiency"]["emotion"] += 1
                        break
                for n_word in self.base["L1_product_efficiency"][L2_keyword][L3_keyword]["normal"]:
                    if n_word in self.jieba_words:
                        self.output["L1_product_efficiency"][L2_keyword][L3_keyword]["match"].append(n_word)
                        self.output["L1_product_efficiency"][L2_keyword][L3_keyword]["emotion"] = 0
                        break
                for b_word in self.base["L1_product_efficiency"][L2_keyword][L3_keyword]["bad"]:
                    if b_word in self.jieba_words:
                        self.output["L1_product_efficiency"][L2_keyword][L3_keyword]["match"].append(b_word)
                        self.output["L1_product_efficiency"][L2_keyword][L3_keyword]["emotion"] = -1
                        self.output["L1_product_efficiency"][L2_keyword]["emotion"] -= 1
                        self.output["L1_product_efficiency"]["emotion"] -= 1
                        break


if __name__ == '__main__':

    input_text = "保湿控油很差，一下就油了，而且浮粉很严重，最难用的粉底液，（我是不容易脱妆的肌肤）无关黑他，如实告知自己使用效果，唉"
    # input_text = " 持妆六小时，已经暗淡了。和肤色接近了。刚刚涂上的时候有点白的过活。个人感觉适合油皮，我是偏干皮，然后需要用力拍，不然会卡粉。 整体评价：不错。 保湿控油情况：控油可有 持久度：还可以吧 妆感效果：雾面 遮瑕效果：还可以，脸上没什么瑕疵。 我的肤质：混合偏干"
    # input_text = " 质地轻薄很好用"
    # input_text = " 第二次购买了，光泽度很好，很水润，不控油，特别喜欢，下次还来！物流也很快昨天买的今天到货"
    # input_text = " 第二次购买了，光泽度很好，很水润，不控油，特别喜欢，下次还来！物流也很快昨天买的今天到货"
    # input_text = " 一直都用美宝莲的东西 粉底液 口号 遮瑕都很好用 就买了一瓶粉底液 送了四件 很合算"
    # input_text = "持久度：太太难用了！！！！不持妆，氧化巨快，而且超级无敌干，本人油皮上脸都是干的！！！！！  遮瑕效果：忍很久了。 妆感效果：重点是很快斑驳。！！！！要买的妹子慎买！"
    # input_text = "用了好几天才来评价，个人觉得蛮不错的，持久效果也好，不干，很好上妆，遮瑕还可以，值得推荐"
    # input_text = "遮瑕不好"
    # input_text = "浮粉脱妆，还巨持妆，脱粉严重，之前一直用这个牌子其他系列的粉底液，但是这个真的难用，不出汗一上午就浮粉脱妆了，更别说出汗了，简直一言难尽"
    # input_text = "整体不错 但是物流不送上门"
    # input_text = "发货神速"
    # input_text = "有点卡粉 而且持妆力差 其他还不错"

    ob = KeywordsBasedAspectOpinion()
    ob.get_output(input_text)

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

