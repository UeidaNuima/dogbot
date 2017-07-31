import getopt
import logging
import multiprocessing
import os
import re
import shlex
import tempfile
import time
from urllib import parse

import requests
from PIL import Image
from bs4 import BeautifulSoup, Tag
from dogbot.cqsdk import CQImage
from mongoengine import QuerySet, Q
from selenium import webdriver

from config import config
from dogbot.cqsdk.utils import reply
from dogbot.models import Class, Unit

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
}
BASE_URL = 'http://wikiwiki.jp/aigiszuki/'
RARITY = '铜铁银金白黑蓝'


class UnitException(Exception):
    pass


def get_status_pic(name):
    """
    获取单位图片. 源来自 http://wikiwiki.jp/aigiszuki/
    :param name: 单位全名. 找不到的话会抛出UnitException.
    :return: 一个PIL的image实例, 可以用save方法保存.
    """
    logging.info("Grabbing ...")

    resp = requests.get(
        BASE_URL + '?' + parse.urlencode({
            "cmd": "edit",
            "page": name
        }, encoding="euc-jp"),
        headers=HEADERS
    )


    # 判断页面是否存在
    match = re.findall("(?<=<textarea name=\"msg\" rows=\"26\" cols=\"100\">)[\s\S]*?(?=</textarea>)", resp.text)
    if match[0] == "":
        raise UnitException("Missing Page")

    table = match[0].split("\n")
    tokens = ['**ステータス', '**[[スキル]]', '**[[スキル覚醒]]', '**[[アビリティ]]', '**クラス特性']
    ids = []
    # 获取这几个section后面的id, 用来当锚点
    for line in table:
        for token in tokens:
            if token in line:
                id = re.findall("(?<=\[#).*?(?=\])", line)[-1]
                ids.append(id)
    # print(repr(ids))

    # 获取属性页面
    resp = requests.get(
        ''.join((
            BASE_URL,
            "?",
            parse.quote(name, encoding="euc-jp")
        )),
        headers=HEADERS
    )

    logging.info("Parsing...")
    # 分析页面
    soup = BeautifulSoup(resp.text, "lxml")

    # 样式
    css = """<style>
          *{padding:0;margin:0;font-size: 95%;}
          body{opacity:0.9;background:white;background-size:800px;width:900px;font-family:"PixelMPlus12", "Pingfang SC","Microsoft Yahei", "Wenquanyi Micro Hei" ;}
          .floatleft, .floatLeft{float: left;margin-right: 3px;}
          .clear{display: block;visibility: visible;min-height: 0;clear: both;}
          a{color: #006FD6;text-decoration: none;outline: none;}
          .wrapTable{width:100%}
          table{border-spacing: 0;margin: 0 0 6px;border: #ccc 1px solid;}
          .style_td {background-color: #fafafa!important;padding: 5px;margin: 1px;border: 1px solid #e0e0e0;}
          .style_th {padding: 5px;margin: 1px;background-color: #EEEEEE;border: 1px solid #e0e0e0;}
          #h3_content_1_1 + .ie5 .style_td, #h3_content_1_5 + .ie5 .style_td{padding: 5px;margin: 1px;background-color: #EEEEEE!important;}
          h3, h1{border-bottom: 1px solid #a2a9b1;font-size: 20px;margin-bottom: 10px;}
          .anchor_super, .jumpmenu {display: none}
          h3 a {color: black!important}
          h4 {margin-bottom: 10px;}
          </style>"""

    for a in soup.find_all("a"):
        # 删掉所有的编辑
        if a and "編集" in str(a):
            a.decompose()

    # utf8
    inner_html = ['<meta charset="utf-8" />', css]

    last_modified_str = soup.find(id='lastmodified').text
    last_modified_day = re.findall('\d\d\d\d-\d\d-\d\d', last_modified_str)[0]
    last_modified_time = re.findall('\d+:\d+:\d+', last_modified_str)[0]
    inner_html.append('<h1>{}</h1><h2>本地更新时间: {}</h2><h2>页面更新时间: {}</h2>'.format(
        name,
        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
        last_modified_day + ' ' + last_modified_time
    ))

    # 拆section
    for id in ids:
        html = soup.find("a", id=id)
        if html:
            html = html.parent
            tag = html.name
            inner_html.append(str(html).replace('\n', ''))
            html = html.findNext('div')
            inner_html.append(str(html).replace('\n', ''))
            for sb in html.next_siblings:
                if type(sb) == Tag:
                    if sb.get('id') == 'h4_content_1_2':
                        break
                if sb.name == tag:
                    break
                inner_html.append(str(sb).replace("\n", ""))
    inner_html = "".join(inner_html)
    # 在temp文件夹下工作
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, 'cache.html'), 'w', encoding='utf-8') as fp:
            fp.write(inner_html)
        logging.info("Capturing...")
        driver = webdriver.PhantomJS()
        driver.get(os.path.join(tmpdir, 'cache.html'))
        # 截图
        driver.save_screenshot(os.path.join(tmpdir, name + ".png"))
        driver.quit()
        logging.info("Converting...")
        # 转换成RGB, 可以小一些, 也方保存成jpg
        image = Image.open(os.path.join(tmpdir, name + ".png")).convert("RGB")
    logging.info("Done!")
    return image


def get_conne_pic(names, sorter=None, hidden_fields=[12, 14, 15, 16, 20, 24]):
    """
    获取圆爹dps表的图片. 提供过滤与排序的功能.
    :param names: str list, 圆爹版的单位名称表. str可为正则.
    :param sorter: 排序列, 为1开始的正整数.
    :param hidden_fields: 要隐藏的列.
    :return: 一个PIL的image实例, 可以用save方法保存.
    """
    logging.info("Grabbing ...")
    resp = requests.get(
        'http://www116.sakura.ne.jp/~kuromoji/aigis_dps.htm',
        headers=HEADERS
    )
    logging.info("Parsing...")
    resp.encoding = 'shift-jis'
    soup = BeautifulSoup(resp.text, "lxml")
    # 找到主表
    table = soup.find('table', id='sorter')
    thead = table.thead
    tbody = table.tbody
    trs = []
    # 遍历参数, 拆出相应的tr

    inexistence = []
    for name in names:
        tds = tbody.find_all(text=re.compile('^' + name + '$'))
        if not tds:
            inexistence.append(name)
            continue
        for td in tds:
            tr = td.parent.parent.parent
            tds_ = tr.find_all('td')
            trs.append(tr.extract())

    if sorter:
        trs.sort(key=lambda tr: int(tr.find_all('td')[sorter - 1].text) if tr.find_all('td')[sorter - 1].text else 0, reverse=True)

    tbody.clear()
    for tr in trs:
        tbody.append(tr)
    # 构造新页面
    new_soup = BeautifulSoup('<html><head><meta charset="utf-8"></head><body></body></html>', 'lxml')
    for css in soup.find_all('link'):
        if css.get('href'):
            css['href'] = 'http://www116.sakura.ne.jp/~kuromoji/' + css.get('href')
            new_soup.html.head.append(css)
    new_soup.html.body.append(table)
    # new_soup.html.body.append(BeautifulSoup('<div id="calc" class="clear"></div>', 'lxml'))

    widths = [3, 7, 10, 1.25, 3.25, 3.25, 3, 3, 2, 2, 2, 3.75, 2.5, 3.25, 3.25, 10.50, 3, 3.25, 3, 2, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25, 3.25]
    width = 0
    for w in widths:
        width += w
    csses = ['<style>']
    for field in hidden_fields:
        width -= widths[field - 1]
        csses.append('.aigis_dps tr td:nth-of-type({}){{display:none}}'.format(field))
        csses.append('.aigis_dps tr th:nth-of-type({}){{display:none}}'.format(field))
    csses.append('</style>')
    new_soup.html.head.append(BeautifulSoup(''.join(csses), 'lxml'))

    # 圆爹页上爬下来的部分css
    new_soup.html.head.append(BeautifulSoup(
        ('<style>'
         'a,abbr,acronym,address,applet,article,aside,audio,b,big,blockquote,body,canvas,caption,center,cite,code,dd,del,details,dfn,div,dl,dt,em,embed,fieldset,figcaption,figure,footer,form,h1,h2,h3,h4,h5,h6,header,hgroup,html,i,iframe,img,ins,kbd,label,legend,li,mark,menu,nav,object,ol,output,p,pre,q,ruby,s,samp,section,small,span,strike,strong,sub,summary,sup,table,tbody,td,tfoot,th,thead,time,tr,tt,u,ul,var,video{{margin:0;padding:0;border:0;font-size:100%;font:inherit;vertical-align:baseline}}article,aside,details,figcaption,figure,footer,header,hgroup,menu,nav,section{{display:block}}body{{line-height:1}}ol,ul{{list-style:none}}blockquote,q{{quotes:none}}blockquote:after,blockquote:before,q:after,q:before{{content:'';content:none}}table{{border-collapse:collapse;border-spacing:0}}'
         'table{{line-height: 1.125;}}'
         'td,th{{vertical-align:middle}}'
         'tr.hyde {{display: table-row;}}'
         'body{{font-size: 70%;width: {}em;font-family:"PixelMPlus12", "Pingfang SC",\"Microsoft Yahei\", \"Wenquanyi Micro Hei\";}}'
         '</style>'.format(width))
        , 'lxml'))

    # 写入html
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, 'cache.html'), 'w', encoding='utf-8') as fp:
            fp.write(str(new_soup))
        logging.info("Capturing...")
        driver = webdriver.PhantomJS()
        driver.get(os.path.join(tmpdir, 'cache.html'))
        driver.save_screenshot(os.path.join(tmpdir, 'cache.png'))
        driver.quit()
        logging.info("Converting...")
        # 转换成RGB, 可以小一些, 也方保存成jpg
        image = Image.open(os.path.join(tmpdir, "cache.png")).convert('RGB')
    logging.info("Done!")
    return inexistence, image


def status_worker(bot, message, name, refresh):
    """
    获取属性图的进程worker.
    """
    full_path = os.path.join(config['cq_root_dir'], config['cq_image_dir'], 'unit', name + '.png')
    if not os.path.exists(os.path.join(config['cq_root_dir'], config['cq_image_dir'], 'unit')):
        os.mkdir(os.path.join(config['cq_root_dir'], config['cq_image_dir'], 'unit'))
    # 没有缓存或者要求刷新的情况
    if not os.path.exists(full_path) or refresh:
        try:
            image = get_status_pic(name)
        except UnitException as e:
            reply(bot, message, str(e))
            return
        except Exception as e:
            reply(bot, message, '汪汪汪? 可能是网络问题, 重试一下吧')
            raise e
            return
        image.save(full_path)
    reply(bot, message, CQImage(os.path.join("unit", name + ".png")))


def status(bot, message):
    """#status [-h] [-f] 单位

    -h    : 打印本帮助
    -f    : 强制刷新
    单位   : 可以是单位黑话, 原名, 也可以是职业名; 懒到一定程度的话可以直接 稀有+职业的形式

    例:
        #status 狗蛋
        #status 猫又 (猫又是职业)
        #status 黑风水 (将被拆成黑+风水)
    """
    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'status':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hf')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, status.__doc__)
        return True

    refresh = False

    # 拆参数
    for o, a in options:
        if o == '-h':
            # 帮助
            reply(bot, message, status.__doc__)
            return True
        elif o == '-f':
            refresh = True

    # 必须要有单位参数
    if len(args) < 1:
        reply(bot, message, status.__doc__)
        return True

    target_name = args[0]

    # 找单位
    target = Unit.objects(Q(name=target_name) | Q(nickname=target_name)).first()

    # 看看是不是职业名
    if not target:
        class_ = Class.objects(Q(name=target_name) | Q(translate=target_name) | Q(nickname=target_name)).first()
        if class_:
            target = Unit.objects(class_=class_)

    # 看看是不是稀有度 + 职业名
    if not target:
        rarity = RARITY.find(target_name[:1])
        if not rarity == -1:
            class_name = target_name[1:]
            class_ = Class.objects(Q(name=class_name) | Q(translate=class_name) | Q(nickname=class_name)).first()
            if not class_:
                reply(bot, message, '没找到职业{}'.format(class_name))
                return True
            target = Unit.objects(Q(class_=class_) & Q(rarity=rarity))

    # 结果是不是一个列表
    if type(target) == QuerySet:
        # 多于一个结果, 返回结果列表
        if len(target) > 1:
            msg = '{}不止一个单位...\n'.format(target_name)
            for unit in target:
                msg += '\n{}'.format(unit.name)
            reply(bot, message, msg)
            return True

        # 只有一个结果, 就是它了
        elif len(target) == 1:
            target = target[0]

    # 怎么还没找到的, 丢人
    if not target:
        reply(bot, message, '没找到{}...'.format(target_name))
        return True

    reply(bot, message, '{}, 汪'.format(target.name))

    # 开一个新进程去抓图
    multiprocessing.Process(target=status_worker, args=(bot, message, target.name, refresh)).start()
    return True

SORTER_ALIAS = {
    'hp': 6,
    'atk': 7,
    'def': 8,
    'mr': 9,
    'dps': 21
}


def conne_worker(bot, message, names, full=False, sorter=None):
    """
    获取圆爹的进程worker.
    """
    file_name = 'conne' + str(int(time.time())) + '.png'
    full_path = os.path.join(config['cq_root_dir'], config['cq_image_dir'], file_name)

    hidden_fields = [12, 14, 15, 16, 20, 24]
    if full:
        hidden_fields = []
    try:
        inexistence, image = get_conne_pic(names, sorter, hidden_fields)
    except Exception as e:
        reply(bot, message, '汪汪汪? 可能是网络问题, 重试一下吧')
        raise e
        return
    if inexistence:
        # 有没找到的话提示哪些没找到ff
        reply(bot, message, '以下单位圆爹站好像没找到: {}'.format(', '.join(inexistence)))

    if not len(inexistence) == len(names):
        # 不是一个都没找到就行
        image.save(full_path)
        reply(bot, message, CQImage(file_name))


def conne(bot, message):
    """#conne [-h] [-f] [-s sorter] 单位...

    -h        : 打印本帮助
    -f        : 输出所有的列. 默认隐藏: 物理一击线, 魔法一击线, 补足, 属性, 600防dps
    -s sorter : 排序. 接受以下参数: hp, atk, def, mr, dps
    单位...    : 可以是单位黑话, 原名, 也可以是职业名. 接受多个单位, 空格隔开.

    注:  圆爹只收录了金以上的单位.

    例:
        #conne 狗蛋
        #conne -s dps 风水
        #conne -f -s atk 狮子奶 冬马
    """
    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'conne':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hfs:')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, conne.__doc__)
        return True

    full_fields = False
    sorter = None

    # 拆参数
    for o, a in options:
        if o == '-h':
            # 帮助
            reply(bot, message, conne.__doc__)
            return True
        elif o == '-f':
            full_fields = True
        elif o == '-s':
            if SORTER_ALIAS.get(a):
                sorter = SORTER_ALIAS.get(a)
            else:
                reply(bot, message, conne.__doc__)
                return True

    # 必须要有单位参数
    if len(args) < 1:
        reply(bot, message, conne.__doc__)
        return True

    names = []

    for target_name in args:

        # 找单位
        target = Unit.objects(Q(name=target_name) | Q(nickname=target_name)).first()

        # 不是单位的话找职业
        if not target:
            class_ = Class.objects(Q(name=target_name) | Q(translate=target_name) | Q(nickname=target_name)).first()
            if class_:
                target = Unit.objects(Q(class_=class_) & Q(rarity__gte=3))

        if not target:
            reply(bot, message, '找不到单位{}...'.format(target_name))
            return True

        if not type(target) == QuerySet:
            target = (target,)

        for unit in target:
            try:
                names.index(unit.conne_name)
            except ValueError:
                names.append(unit.conne_name)

    reply(bot, message, '汪')
    # 开一个新进程去抓图
    multiprocessing.Process(target=conne_worker, args=(bot, message, names, full_fields, sorter)).start()
    return True


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s: %(message)s',
                        datefmt='%d %b %Y %H:%M:%S',
                        filename='unit.log',
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info("Running...")
    get_conne_pic(('シビラ', 'リリア', 'テミス', 'スクハ'), 21)
    # get_status_pic('刻詠の風水士リンネ')
