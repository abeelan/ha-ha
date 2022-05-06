"""
@Time   : 2022/5/5 下午4:09
@Author : lan
@Mail   : lanzy.nice@gmail.com
@Desc   : 删除微博，取消关注
"""

import requests

from time import sleep
from loguru import logger
from random import randint

from requests_html import HTMLSession, Element

sec = randint(2, 8)  # API 请求间隔


ST = "定位到取消关注或者删除微博的元素上，在 href 属性里面找到 st 对应的值粘贴过来"
COOKIES = '网页版登录后，打开开发者工具 Network，刷新页面，请求头内找到 cookie，把值粘贴过来'


class WeiBo:

    HOST = "https://weibo.cn"
    USER_AGENT = "Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) " \
                 "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36"

    def __init__(self, uid, flag=1):
        self.headers = {
            'user-agent': self.USER_AGENT,
            'cookie': COOKIES
        }
        self.session = HTMLSession()
        self.session.headers = self.headers

        self.uid = str(uid)
        self.flag = int(flag)  # 1 删除全部微博；2 取消全部关注
        self.total_weibo_pages = 0   # 已发表微博总页数，每页 10 条
        self.total_follow_pages = 0  # 已关注用户总页数，每页 10 个

        # URL
        self.url_info = f"{self.HOST}/{self.uid}/info"
        self.url_profile = f"{self.HOST}/{self.uid}/profile"  # Default page=1
        self.url_del_weibo = f"{self.HOST}/mblog/del"
        self.url_follow = f"{self.HOST}/{self.uid}/follow"
        self.url_del_follow = f"{self.HOST}/attention/del"

        # 用户信息，从 profile 获取
        self.post = 0    # 发表微博数
        self.follow = 0  # 关注人数
        self.fans = 0    # 粉丝人数

        # 初始化
        self.get_weibo_list_page()
        self.get_user_info()

        self.run(flag=self.flag)

    def get_user_info(self):
        """获取用户信息"""
        r = self.session.get(self.url_info)
        html = r.html

        obj_list = html.find("div.c")
        vip_info = obj_list[4].text
        user_info = obj_list[5].text

        logger.info(
            f"\n{'='*10} 用户信息 {'='*10}\n"
            f"{user_info}\n\n"
            f"{vip_info}\n\n"
            f"{self.post} {self.follow} {self.fans}\n"
            f"{'='*30}"
        )

    def get_weibo_list_page(self, page: int = 1) -> list:
        """ 进入我的微博页面，根据页数，返回每页最多 10 个微博内容对象
            [<Element 'div' class=('c',) id='M_LbMX2jwOX'>, ...]
        """
        r = self.session.get(self.url_profile, params={"page": page})
        html = r.html

        # 获取总页数
        if self.total_weibo_pages == 0:
            try:
                page_nums_str: str = html.find("div.pa", first=True).text
                self.total_weibo_pages = int(page_nums_str.split("/")[-1].replace("页", ""))
            except AttributeError:
                self.total_weibo_pages = 1

        # 获取用户信息
        self.post = html.find("div.tip2 span.tc", first=True).text
        self.follow = html.find("div.tip2 a")[0].text
        self.fans = html.find("div.tip2 a")[1].text

        # 获取当前页微博
        weibo_objs: list = html.find("div.c")
        weibo_objs.remove(weibo_objs[0])  # 页头
        weibo_objs.remove(weibo_objs[-1])  # 页尾
        return weibo_objs

    def get_single_weibo_id(self, weibo_obj: Element):
        """获取单条微博内容"""
        weibo_id = weibo_obj.attrs["id"].split("_")[-1]
        content = weibo_obj.find("span.ctt", first=True).text
        posted_time = weibo_obj.find("span.ct", first=True).text

        logger.info(f"【 ID  】{weibo_id}")
        logger.info(f"【 时间 】{posted_time}")
        logger.info(f"【 内容 】{content}")

        return weibo_id

    def del_single_weibo(self, weibo_id) -> bool:
        """删除单条微博"""
        params = {
            "type": "del",
            "act": "delc",
            "rl": "1",
            "st": ST,
            "id": weibo_id
        }
        r = requests.get(url=self.url_del_weibo, params=params, headers=self.headers)
        if r.status_code != 200:
            return False
        logger.success(f"删除成功: {weibo_id}")
        return True

    def del_all_weibo(self):
        self.get_weibo_list_page()  # 获取微博总页数
        del_nums = 0  # 删除微博数统计

        for i in range(1, self.total_weibo_pages):
            logger.info(f"******* 删除微博，第 {i} 页 *******")
            objs = self.get_weibo_list_page(page=i)

            for obj in objs:
                logger.debug(f"NEXT({obj}) ==> ")
                weibo_id = self.get_single_weibo_id(obj)
                if self.del_single_weibo(weibo_id):
                    del_nums += 1
                    logger.info(f"当前已删除微博总数为: {del_nums}.")
                sleep(sec)

    def get_follow_list_page(self, page=1) -> list:
        """ 根据页数获取我的关注页面的内容
            [<Element>, ...]
        """
        r = self.session.get(self.url_follow, params={"page": page})
        # logger.info(r.url)
        html = r.html

        # 获取总页数
        if self.total_follow_pages == 0:
            try:
                page_nums_str: str = html.find("div.pa", first=True).text
                self.total_follow_pages = int(page_nums_str.split("/")[-1].replace("页", ""))
            except AttributeError:
                self.total_follow_pages = 1

        # 获取被关注人对象（每页最多 10 个）
        follow_objs = html.find("table tr")
        return follow_objs

    def get_single_uid(self, user_obj: Element):
        """获取被关注用户 ID"""
        uid = None

        elements = user_obj.find("a")
        name = elements[1].text
        for e in elements:
            link = e.attrs["href"]
            if "uid" in link:
                params = link.split("?")[-1].split("&")
                for p in params:
                    if "uid" in p:
                        uid = p.split("=")[-1]
                        break

        logger.info(f"当前被关注用户为: {name}({uid})")
        return uid

    def del_single_follow(self, uid):
        """取消关注, uid 为被关注用户的 ID"""
        headers = {
            **self.headers,
            **{"referer": self.url_del_follow + f"?uid={uid}&rl=1&st={ST}"}
        }
        params = {
            "rl": "1",
            "act": "delc",
            "uid": uid,
            "st": ST
        }
        r = requests.get(self.url_del_follow, params=params, headers=headers)
        # logger.debug(r.url)
        # logger.debug(r.text)
        if r.status_code == 200 and "首页" not in r.text:
            logger.success(f"取消关注成功: {uid}")
            return True
        return False

    def del_all_follow(self):
        """取消全部关注"""
        self.get_follow_list_page()  # 获取关注总页数
        del_nums = 0  # 取消关注数统计

        for i in range(1, self.total_follow_pages):
            logger.info(f"******* 取消关注，第 {i} 页 *******")
            objs = self.get_follow_list_page(page=i)

            for obj in objs:
                uid = self.get_single_uid(obj)
                if self.del_single_follow(uid):
                    del_nums += 1
                    logger.info(f"取消关注总人数为: {del_nums}.\n")
                sleep(sec)

    def run(self, flag=1):
        """ flag: 1 删除全部微博；2 取消全部关注
        """
        if flag == 1:
            func = self.del_all_weibo
        elif flag == 2:
            func = self.del_all_follow
        else:
            logger.warning("Please enter parameters -> flag=(1 | 2).")
            return

        try:
            func()
        except requests.exceptions.SSLError:
            logger.warning("请求过多，请稍后再试！")


if __name__ == '__main__':
    weibo = WeiBo(uid=123456789, flag=2)

