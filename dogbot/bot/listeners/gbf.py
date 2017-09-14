import re
import requests
from dogbot.cqsdk.utils import reply

GBF_PATTERN = re.compile("^((https|http|ftp|rtsp|mms)?://)"  # 端口
                         "?(([0-9a-z_!~*'().&=+$%-]+: )?[0-9a-z_!~*'().&=+$%-]+@)?"  # ftp 用戶密碼
                         "(([0-9]{1,3}\.){3}[0-9]{1,3}"  # IP URL
                         "|"
                         "([0-9a-z_!~*'()-]+\.)*"  # 域名前綴
                         "([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\."  # 二級域名
                         "[a-z]{2,6})"  # 頂級域名
                         "(:[0-9]{1,4})?"  # 端口
                         "((/?)|"  # 路徑
                         "(/[0-9a-z_!~*'().;?:@&=+$,%#-]+)+/?)$")

match_urls = []


def gbf(bot, message):
    result = GBF_PATTERN.findall(message.text)
    for index, match in enumerate(result):
        if index > 10:
            return False
        url = match[0]
        if url not in match_urls:
            resp = requests.get('url')
            if 'granblue' in resp.url:
                match_urls.append(url)
                reply(bot, message, '碧蓝幻想，请勿访问')
                return True
        else:
            reply(bot, message, '碧蓝幻想，请勿访问')
            return True
