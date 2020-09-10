# -*-coding:utf-8 -*-

'''
@File       : manager.py
@Author     : HW Shen
@Date       : 2020/9/9
@Desc       :
'''

import tornado.web
from loguru import logger
from tornado.ioloop import IOLoop
from tornado.web import URLSpec
from TargetSocialNlpService.func.handler import WordCloudHandler


HANDLERS = [
    URLSpec(r'/wordcloud', WordCloudHandler, name=WordCloudHandler.__name__),  # 词云统计接口
]


if __name__ == '__main__':

    # 日志文件
    logger.add("log/file_{time}.log")

    SERVER_PORT = 5555
    SERVER_IP = "127.0.0.1"

    app = tornado.web.Application(handlers=HANDLERS, debug=True)
    app.listen(SERVER_PORT, SERVER_IP)

    logger.info("Clean Panel server started on port {SERVER_IP}:{SERVER_PORT}".format(SERVER_PORT=SERVER_PORT, SERVER_IP=SERVER_IP))
    IOLoop.current().start()

