#!/usr/bin/env python3

import re
import sys
import traceback
from base64 import b64encode, b64decode
from collections import namedtuple
import socket
import socketserver
from apscheduler.schedulers.background import BackgroundScheduler
import threading

ClientHello = namedtuple("ClientHello", ("port"))
ServerHello = namedtuple("ServerHello", ())

RcvdPrivateMessage = namedtuple("RcvdPrivateMessage", ("qq", "text"))
SendPrivateMessage = namedtuple("SendPrivateMessage", ("qq", "text"))

RcvdGroupMessage = namedtuple("RcvdGroupMessage", ("group", "qq", "text"))
SendGroupMessage = namedtuple("SendGroupMessage", ("group", "text"))

RcvdDiscussMessage = namedtuple("RcvdDiscussMessage",
                                ("discuss", "qq", "text"))
SendDiscussMessage = namedtuple("SendDiscussMessage",
                                ("discuss", "text"))

GroupMemberDecrease = namedtuple("GroupMemberDecrease",
                                 ("group", "qq", "operatedQQ"))
GroupMemberIncrease = namedtuple("GroupMemberIncrease",
                                 ("group", "qq", "operatedQQ"))
GroupBan = namedtuple("GroupBan", ("group", "qq", "duration"))

Fatal = namedtuple("Fatal", ("text"))

FrameType = namedtuple("FrameType", ("prefix", "rcvd", "send"))
FRAME_TYPES = (
    FrameType("ClientHello", (), ClientHello),
    FrameType("ServerHello", ServerHello, ()),
    FrameType("PrivateMessage", RcvdPrivateMessage, SendPrivateMessage),
    FrameType("DiscussMessage", RcvdDiscussMessage, SendDiscussMessage),
    FrameType("GroupMessage", RcvdGroupMessage, SendGroupMessage),
    FrameType("GroupMemberDecrease", GroupMemberDecrease, ()),
    FrameType("GroupMemberIncrease", GroupMemberIncrease, ()),
    FrameType("GroupBan", (), GroupBan),
    FrameType("Fatal", (), Fatal),
)

RE_CQ_SPECIAL = re.compile(r'\[CQ:\w+(,.+?)?\]')


class CQAt:
    PATTERN = re.compile(r'\[cq:at,qq=(\d+?)\]')

    def __init__(self, qq):
        self.qq = qq

    def __str__(self):
        return "[CQ:at,qq={}]".format(self.qq)


class CQImage:
    PATTERN = re.compile(r'\[CQ:image,file=(.+?)\]')

    def __init__(self, file):
        self.file = file

    def __str__(self):
        return "[CQ:image,file={}]".format(self.file)


def load_frame(data):
    if isinstance(data, str):
        parts = data.split()
    elif isinstance(data, list):
        parts = data
    else:
        raise TypeError()

    frame = None
    (prefix, *payload) = parts
    for type_ in FRAME_TYPES:
        if prefix == type_.prefix:
            frame = type_.rcvd(*payload)
    # decode text
    if isinstance(frame, (
            RcvdPrivateMessage, RcvdGroupMessage, RcvdDiscussMessage)):
        payload[-1] = b64decode(payload[-1]).decode('gbk')
        frame = type(frame)(*payload)
    return frame


def dump_frame(frame):
    if not isinstance(frame, (tuple, list)):
        raise TypeError()

    # Cast all payload fields to string
    payload = list(map(lambda x: str(x), frame))

    # encode text
    if isinstance(frame, (
            SendPrivateMessage, SendGroupMessage, SendDiscussMessage, Fatal)):
        payload[-1] = b64encode(payload[-1].encode('gbk')).decode()

    data = None
    for type_ in FRAME_TYPES:
        if isinstance(frame, type_.send):
            data = " ".join((type_.prefix, *payload))
    return data


class FrameListener:
    def __init__(self, handler, frame_type):
        self.handler = handler
        self.frame_type = frame_type


class APIRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].decode()
        parts = data.split()

        try:
            message = load_frame(parts)
        except:
            message = None
        if message is None:
            print("Unknown message", parts, file=sys.stderr)
            return

        threading.Thread(target=self.listen, args=(message, ), daemon=True).start()


    def listen(self, message):
        for listener in self.server.bot.listeners:
            try:
                if isinstance(message, listener.frame_type):
                    blocked = listener.handler(self.server.bot, message)
                    if blocked:
                        # 中间改变了message
                        if isinstance(blocked, (RcvdDiscussMessage, RcvdGroupMessage, RcvdPrivateMessage)):
                            message = blocked
                            continue
                        break
            except:
                traceback.print_exc()


class CQBot:
    def __init__(self, server_port, client_port, online=True, debug=False):
        self.listeners = []

        self.remote_addr = ("127.0.0.1", server_port)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.local_addr = ("127.0.0.1", client_port)
        self.server = socketserver.UDPServer(self.local_addr, APIRequestHandler)
        self.server.bot = self
        # Online mode
        #   True: Retrive message from socket API server
        #   False: Send message only
        self.online = online

        # Debug Mode
        #   True: only send private message.
        self.debug = debug

        self.scheduler = BackgroundScheduler(
            timezone='Asia/Tokyo',
            job_defaults={'misfire_grace_time': 60},
        )

        self.scheduler.add_job(self.server_keepalive, 'interval', seconds=30)


    def __del__(self):
        self.client.close()
        # self.server.shutdown()

    def start(self):
        if not self.online:
            return

        self.scheduler.start()
        self.server.serve_forever()

    def server_keepalive(self):
        host, port = self.server.server_address
        self.send(ClientHello(port))

    def listener(self, frame_type):
        def decorator(handler):
            self.listeners.append(FrameListener(handler, frame_type))
        return decorator

    def add_listener(self, handler, frame_type):
        self.listeners.append(FrameListener(handler, frame_type))

    def send(self, message):
        if self.debug:
            print(message)
            if not isinstance(message, (SendPrivateMessage, ClientHello)):
                return
        data = dump_frame(message).encode()
        self.client.sendto(data, self.remote_addr)


if __name__ == '__main__':
    try:
        qqbot = CQBot(12450, 11235)

        @qqbot.listener((RcvdPrivateMessage, ))
        def log(message):
            print(message)

        qqbot.send(SendPrivateMessage(qq=123123, text='#emoji -d test'))
        # qqbot.start()

        print("QQBot is running...")
    except KeyboardInterrupt:
        pass
