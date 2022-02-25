
class BaseBot:
    def __init__(self):
        self.message_types = [1,3,34,43,47,49]
        self._handlers = {k: [] for k in self.message_types}
    
    def get_handlers(self, type):
        return self._handlers.get(type, [])

    def add_handler(self, func, type='all'):
        """
        为 BaseRoBot 实例添加一个 handler。

        :param func: 要作为 handler 的方法。
        :param type: handler 的种类。
        :return: None
        """
        if not callable(func):
            raise ValueError("{} is not callable".format(func))

        self._handlers[type].append(func)

    def handler(self, f):
        """
        为每一条消息或事件添加一个 handler 方法的装饰器。
        """
        self.add_handler(f, type='all')
        return f
    
    def filter(self, *args):
        """
        为文本 ``(text)`` 消息添加 handler 的简便方法。

        使用 ``@filter("xxx")``, ``@filter(re.compile("xxx"))``
        或 ``@filter("xxx", "xxx2")`` 的形式为特定内容添加 handler。
        """
        def wraps(f):
            self.add_filter(func=f, rules=list(args))
            return f

        return wraps

    def add_filter(self, func, rules):
        """
        为 BaseRoBot 添加一个 ``filter handler``。

        :param func: 如果 rules 通过，则处理该消息的 handler。
        :param rules: 一个 list，包含要匹配的字符串或者正则表达式。
        :return: None
        """
        if not callable(func):
            raise ValueError("{} is not callable".format(func))
        if not isinstance(rules, list):
            raise ValueError("{} is not list".format(rules))
        if len(rules) > 1:
            for x in rules:
                self.add_filter(func, [x])
        else:
            target_content = rules[0]
            def _check_content(message):
                return target_content.match(message['Content'])
            @self.text
            def _f(message):
                _check_result = _check_content(message)
                if _check_result:
                    if isinstance(_check_result, bool):
                        _check_result = None
                    return func(message)

    def text(self, f):
        """
        为文本 ``(text)`` 消息添加一个 handler 方法的装饰器。
        """
        self.add_handler(f, type=1)
        return f

    def image(self, f):
        """
        为图像 ``(image)`` 消息添加一个 handler 方法的装饰器。
        """
        self.add_handler(f, type=3)
        return f

    def voice(self, f):
        """
        为语音 ``(voice)`` 消息添加一个 handler 方法的装饰器。
        """
        self.add_handler(f, type=34)
        return f

    def video(self, f):
        """
        为视频 ``(video)`` 消息添加一个 handler 方法的装饰器。
        """
        self.add_handler(f, type=43)
        return f
    
    def bqb(self, f):
        """
        为视频 ``(video)`` 消息添加一个 handler 方法的装饰器。
        """
        self.add_handler(f, type=47)
        return f
    
    def card(self, f):
        """
        卡片消息：文件、音乐、公众号文章、外部链接
        """
        self.add_handler(f, type=49)
    