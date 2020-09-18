# -*-coding:utf-8 -*-

'''
@File       : handler.py
@Author     : HW Shen
@Date       : 2020/9/9
@Desc       :
'''


import abc
import json
from abc import ABC
from concurrent.futures import ThreadPoolExecutor
import tornado.web
from loguru import logger
from tornado import gen
from tornado.concurrent import run_on_executor
from tornado.web import HTTPError
from TargetSocialNlpService.func.word_cloud import GenerateWordCloud
from TargetSocialNlpService.func.kw_based_aspect_opinion import KeywordsBasedAspectOpinion


NUMBER_OF_EXECUTOR = 16  # 线程池的数量


class BaseHandler(tornado.web.RequestHandler):
    """ Tornado Post 基类 """

    # 必须定义一个executor的属性，run_on_executor装饰器才会发挥作用
    executor = ThreadPoolExecutor(NUMBER_OF_EXECUTOR)

    @tornado.web.asynchronous  # 保持长连接，直到处理后返回
    @gen.coroutine  # 异步、协程处理；增加并发量
    def post(self, *args, **kwargs):
        try:
            result = yield self._post(*args, **kwargs)
            # print("result: ", result)
            self.write(result)
        except HTTPError as e:
            self.write(e)
        except Exception as e:
            logger.error(e)
            raise HTTPError(404, "No results")

    @run_on_executor  # 线程内运行；query函数被run_on_executor包裹(语法糖)，将该函数的执行传递给线程池executor的线程执行，优化了处理耗时性任务，以致达到不阻塞主线程的效果。
    def _post(self, *args, **kwargs):
        request = self._post_request_arguments(*args, **kwargs)
        res = self._request_service(**request)
        return res

    @abc.abstractmethod
    def _post_request_arguments(self, *args, **kwargs):
        raise NotImplementedError('call to abstract method %s._get_request_arguments' % self.__class__)

    @abc.abstractmethod
    def _request_service(self, **kwargs):
        raise NotImplementedError('call to abstract method %s._request_service' % self.__class__)


class WordCloudHandler(BaseHandler, ABC):
    """ 词云展示子类 """

    def _post_request_arguments(self, *args, **kwargs):
        '''
        获取数据
        '''
        logger.info(self.__class__.__name__)

        data = json.loads(self.request.body)
        if not data:
            raise HTTPError(400, "Query argument cannot be empty string")
        return data

    def _request_service(self, text):
        '''
        request请求处理
        '''
        if text:
            gwc = GenerateWordCloud()
            res = gwc.get_phrases_freq(text)
        else:
            raise HTTPError(400, "Query argument cannot be empty string")
        return res


class SentimentHandler(BaseHandler, ABC):
    """ 情感分析子类 """

    def _post_request_arguments(self, *args, **kwargs):
        '''
        获取数据
        '''
        logger.info(self.__class__.__name__)

        data = json.loads(self.request.body)
        if not data:
            raise HTTPError(400, "Query argument cannot be empty string")
        return data

    def _request_service(self, text):
        '''
        request请求处理
        '''
        if text:
            kbao = KeywordsBasedAspectOpinion()
            res = kbao.get_output(text)
        else:
            raise HTTPError(400, "Query argument cannot be empty string")
        return res