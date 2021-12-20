"""
@Time   : 2021/12/14 下午12:21
@Author : lan
@Mail   : lanzy.nice@gmail.com
@Desc   : 移动运营商；每日签到
"""
import requests
from loguru import logger

# 连接代理工具，抓包请求内参数
token = "123456789-ha-ha"
# 使用账号密码登录，抓包请求，把加密串复制过来
ef = None


class MobileSign:

    def __init__(self):
        self.url = "https://mobilebj.cn/app/"
        self.token = token

        self.session = requests.Session()
        self.session.headers = {
            "Accept": "*/*",
            "User-Agent": "okhttp/2.5.0",
            "Connection": "keep-alive"
        }

        # 登录的 cookie 写在这里
        cookie_dict = {}
        cookies = requests.utils.cookiejar_from_dict(cookie_dict)
        self.session.cookies = cookies

    def request(self, data) -> requests.Response.json:
        r = self.session.request(**data)
        r.raise_for_status()
        result = r.json()

        logger.debug(f"[Request ] {r.url}")
        logger.debug(f"[Response] {result}")

        return result

    def login(self) -> requests.Response.json:
        if not ef:
            logger.error(f"登录失败，请填写全局变量 'ef' 的值后重试！")
            raise ValueError(f"Please set the 'ef' value, now {ef}.")

        data = {
            "url": self.url + "websitepwdLogin",
            "method": "get",
            "params": {
                "ef": ef,
                "ver": "bjservice_and_8.2.0"
            }
        }
        result = self.request(data)

        # 重新赋值 token，如果过期先手动修改一下全局变量 token 吧
        # TODO: 这里需要读写文件，新 token 替换掉全局变量 token
        self.token = result["token"]
        logger.info(f"[ Token 更新: {self.token} ]")

        return result

    def sign(self) -> requests.Response.json:
        logger.info("开始签到 >>>")

        data = {
            "url": self.url + "signIn",
            "method": "get",
            "params": {"token": self.token}
        }
        result = self.request(data)

        logger.info("<<< 签到请求完成")

        return result

    def get_sign_info(self) -> requests.Response.json:
        logger.info("获取当前签到状态 >>>")
        data = {
            "url": self.url + "querySignInfo",
            "method": "get",
            "params": {"token": self.token}
        }
        result = self.request(data)

        logger.info(f"手机号码:\t{result.get('phone')}")
        logger.info(f"签到状态:\t{result.get('is_signed')}")
        logger.info(f"累计签到数:\t{result.get('total_times')}")
        logger.info(f"本月签到数:\t{result.get('month_times')}")
        logger.info(f"连续签到数:\t{result.get('continue_times')}")
        logger.info("<<< 签到状态获取完毕")
        return result

    def run(self):
        sign_info = self.get_sign_info()
        sign_result = sign_info.get("result")

        if sign_result == "-99999":
            # token 过期
            # {'result': '-99999', 'errmsg': '您好，当前访问状态已经超时了，请您重新登录~'}
            logger.info(f"[ Token 过期: {self.token} ] {sign_info.get('errmsg')}")
            self.login()

        if sign_info.get("is_signed") is True:
            logger.info("今天已经签过到了！")
            return

        self.sign()
        assert self.get_sign_info()["is_signed"] is True


if __name__ == '__main__':
    MobileSign().run()
