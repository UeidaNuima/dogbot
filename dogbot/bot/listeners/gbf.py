import re
import requests
from requests.exceptions import  MissingSchema
from dogbot.cqsdk.utils import reply

GBF_PATTERN = re.compile("(((https|http|ftp|rtsp|mms)?://)"  # 端口
                         "?(([0-9a-z_!~*'().&=+$%-]+: )?[0-9a-z_!~*'().&=+$%-]+@)?"  # ftp 用戶密碼
                         "(([0-9]{1,3}\.){3}[0-9]{1,3}"  # IP URL
                         "|"
                         "([0-9a-z_!~*'()-]+\.)*"  # 域名前綴
                         "([0-9a-zA-Z][A-Z0-9a-z-]{0,61})?[0-9a-zA-Z]\."  # 二級域名
                         "[a-z]{2,6})"  # 頂級域名
                         "(:[0-9]{1,4})?"  # 端口
                         "(/[0-9a-zA-Z_!~*'().;?:@&=+$,%#-]+)*/?)")  # 路徑

match_urls = []


def gbf(bot, message):
    result = GBF_PATTERN.findall(message.text)
    for index, match in enumerate(result):
        if index > 10:
            return False
        url = match[0]
        if url.split('.')[-1] in ['png', 'jpg', 'jpeg', 'gif']:
            return False
        if url not in match_urls:
            try:
                resp = requests.get(url)
            except MissingSchema:
                resp = requests.get('http://' + url)
            if 'granblue' in resp.url:
                match_urls.append(url)
                reply(bot, message, '碧蓝幻想，请勿访问')
                return True
        else:
            reply(bot, message, '碧蓝幻想，请勿访问')
            return True
