import getopt
import shlex

from config import config
from dogbot.cqsdk.utils import reply
from dogbot.models import *

BUCKET_EXP = 8000
SMALL_BLESS_EXP = {
    2: 4000,
    3: 18000,
    4: 19000,
    5: 20000,
    6: 19000
}
IKUSEI_FIX = 1.1
RARITY = '铜铁银金白黑蓝'


class ExpException(Exception):
    pass


class ExpCalc:
    def __init__(self, rarity):
        self.rarity = rarity

    def count_buckets(self, start_lv, end_lv, use_ikusei=False):
        """计算从start_lv到end_lv一共需要多少桶并且给出整桶建议

        :param start_lv: int 初始等级
        :param end_lv: int 目标等级
        :param use_ikusei: bool 是否使用育成圣灵
        :return: dict
            bucket: float 需要的桶数
            suggest: dict 见count_start
            error: str 错误信息, 当出错时被填充
        """
        if start_lv >= end_lv:
            raise ExpException('目标等级要大于初始等级')
        if end_lv >= 100:
            raise ExpException('大于等于100')
        per_bucket_exp = BUCKET_EXP if not use_ikusei else BUCKET_EXP * IKUSEI_FIX
        exp = Exp.objects(Q(rarity=self.rarity) & Q(lv__gte=start_lv) & Q(lv__lt=end_lv)).sum('exp')
        bucket = exp / per_bucket_exp
        ret = {'bucket': bucket}
        bucket_rounded = int(bucket)
        sum_exp = bucket_rounded * per_bucket_exp
        try:
            suggest = self.count_start(end_lv=end_lv, bucket=bucket_rounded, use_ikusei=use_ikusei)
            ret['suggest'] = suggest
        except ExpException as e:
            pass

        return ret

    def count_start(self, end_lv, bucket=0, small_bless=0, use_ikusei=False):
        """计算应该从哪一级开始使用bucket个桶small_bless个小祝福能正好到end_lv.

        :param end_lv: int 目标等级
        :param bucket: int 桶数
        :param small_bless: int 小祝福数
        :param use_ikusei: bool 使用育成圣灵
        :return: dict
            lv: 等级
            remain_exp: 这级到下一级的经验
            error: 错误信息, 当出错时被填充
        """
        if end_lv >= 100:
            raise ExpException('大于等于100')
        if not bucket:
            bucket = 0
        sum_exp = int(bucket * BUCKET_EXP)
        if small_bless:
            if not 2 <= self.rarity <= 6:
                raise ExpException('这个稀有度没有小祝福')
            sum_exp += small_bless * SMALL_BLESS_EXP[self.rarity]
        if not bucket and not small_bless:
            raise ExpException('桶和小祝福至少要有一个')
        if use_ikusei:
            sum_exp *= IKUSEI_FIX
        ret = {'sum_exp': sum_exp}
        for current_lv in range(end_lv - 1, 0, -1):
            exp = Exp.objects(Q(rarity=self.rarity) & Q(lv__gte=current_lv) & Q(lv__lt=end_lv)).sum('exp')
            if exp >= sum_exp:
                ret['lv'] = current_lv
                ret['remain_exp'] = Exp.objects(Q(rarity=self.rarity) & Q(lv=current_lv)).first().exp - (exp - sum_exp)
                break
        else:
            raise ExpException('经验超出范围')
        return ret


def bucket(bot, message):
    """#exp [-h] [-b 桶数] [-s 小祝福数] 稀有度 [start_lv] end_lv

    -h         : 打印本帮助
    -b 桶数     : 桶数, 整数
    -s 小祝福数 : 小祝福数, 整数
    稀有度      : 稀有度, 可以是铜铁银金白黑蓝
    start_lv   : 当前等级
    end_lv     : 目标等级

    例:
        #exp -b 2 黑 50 黑卡多少级到50级正好2桶
        #exp 蓝 10 50 蓝从10级到50级一共要多少桶
    """

    try:
        cmd, *args = shlex.split(message.text)
    except ValueError:
        return False
    if not cmd[0] in config['trigger']:
        return False
    if not cmd[1:] == 'exp':
        return False
    try:
        options, args = getopt.gnu_getopt(args, 'hb:s:')
    except getopt.GetoptError:
        # 格式不对
        reply(bot, message, bucket.__doc__)
        return True

    # 拆参数
    bkt = None
    bless = None
    try:
        for o, a in options:
            if o == '-b':
                # 桶数
                bkt = int(a)
            elif o == '-s':
                # 小祝福数
                bless = int(a)
            elif o == '-h':
                # 帮助
                reply(bot, message, bucket.__doc__)
                return True
    except ValueError:
        # 就是不输数字什么的
        reply(bot, message, bucket.__doc__)
        return True

    if len(args) < 2:
        # 至少要有稀有度和目标等级
        reply(bot, message, bucket.__doc__)
        return True
    rarity = RARITY.find(args[0])
    if rarity == -1:
        # 不是铜铁银金白黑蓝之一
        reply(bot, message, bucket.__doc__)
        return True


    start_lv = None
    end_lv = None

    try:
        if len(args) == 2:
            end_lv = int(args[1])
        else:
            start_lv, end_lv = int(args[1]), int(args[2])
    except ValueError:
        reply(bot, message, bucket.__doc__)
        return True

    calc = ExpCalc(rarity)

    if start_lv:
        # 从某级到某级要多少桶
        try:
            msg_frag = ['[{}]{:.2f}个桶', ', {}到下一级{:.0f}经验{}个']
            msg = []

            res = calc.count_buckets(start_lv, end_lv)
            msg.append(msg_frag[0].format(BUCKET_EXP, res['bucket']))
            if res.get('suggest') and not int(res['bucket']) == 0:
                msg.append(msg_frag[1].format(
                    res['suggest']['lv'],
                    res['suggest']['remain_exp'],
                    int(res['bucket'])
                ))

            msg.append('\n')
            res_ikusei = calc.count_buckets(start_lv, end_lv, True)
            msg.append(msg_frag[0].format(int(BUCKET_EXP * IKUSEI_FIX), res_ikusei['bucket']))
            if res_ikusei.get('suggest') and not int(res_ikusei['bucket']) == 0:
                msg.append(msg_frag[1].format(
                    res_ikusei['suggest']['lv'],
                    res_ikusei['suggest']['remain_exp'],
                    int(res_ikusei['bucket'])
                ))

            reply(bot, message, ''.join(msg))

        except ExpException as e:
            reply(bot, message, str(e))
            return True

    else:
        # 用多少桶到某级要从几级开始喂
        msg_frag = '[{sum_exp:.0f}]{lv}级到下一级{remain_exp:.0f}经验'
        msg = []

        try:
            msg.append(msg_frag.format(**calc.count_start(end_lv, bkt, bless)))
        except ExpException as e:
            reply(bot, message, str(e))
            return True

        try:
            msg.append(msg_frag.format(**calc.count_start(end_lv, bkt, bless, True)))
        except ExpException as e:
            msg.append(str(e))
        reply(bot, message, '\n'.join(msg))
        return True

    return True


if __name__ == '__main__':
    from mongoengine import connect
    connect('aigis')
    print(ExpCalc(5).count_buckets(1, 50))
    print(ExpCalc(5).count_start(50, 0, 1))
