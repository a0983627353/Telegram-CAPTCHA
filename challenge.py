from abc import ABC, abstractmethod
import random
import re

import mwclient


class Challenge(ABC):
    @abstractmethod
    def new(self):
        pass

    @abstractmethod
    def qus(self):
        pass

    @abstractmethod
    def ans(self):
        pass

    @abstractmethod
    def choices(self):
        pass


class MathChallenge(Challenge):
    """
    Thanks to fossifer, who authored this class.
    Link: https://github.com/fossifer/Telegram-CAPTCHA-bot/blob/master/challenge.py
    License: MIT
    """

    def __init__(self):
        self._a = 0
        self._b = 0
        self._op = '+'
        self._ans = 0
        self._choices = []
        self.new()

    def __str__(self):
        return '{a}{op}{b}=?'.format(a=self._a, b=self._b, op=self._op)

    def new(self):
        operation = random.choice(['+', '-', '×', '÷'])
        a, b, ans = 0, 0, 0
        if operation in ['+', '-']:
            a, b = random.randint(0, 50), random.randint(0, 50)
            a, b = max(a, b), min(a, b)
            ans = a + b if operation == '+' else a - b
        elif operation == '×':
            a, b = random.randint(0, 9), random.randint(0, 9)
            ans = a * b
        elif operation == '÷':
            a, b = random.randint(0, 9), random.randint(1, 9)
            ans = a
            a = a * b

        cases = 6
        choices = random.sample(range(100), cases)
        if ans not in choices:
            choices[0] = ans
        random.shuffle(choices)
        # Some bots just blindly click the first button
        if choices[0] == ans:
            choices[0], choices[1] = choices[1], choices[0]

        self._a, self._b = a, b
        self._op = operation
        self._ans = ans
        self._choices = choices

    def qus(self):
        return self.__str__()

    def ans(self):
        return self._ans

    def choices(self):
        return self._choices


class TextReadingChallenge(Challenge):
    site = mwclient.Site('zh.wikipedia.org')

    def __init__(self, qus_template: str):
        """
        :param qus_template: Template message for question. Use string prepared for str.format() method.
                             Required arguments are {text} and {index}
        """
        self._text = ''
        self.ans_index = 0
        self.template = qus_template
        self._ans = ''
        self._choices: list[str] = []
        self.new()

    def new(self):
        random_title = next(TextReadingChallenge.site.random(0, limit=1))['title']
        api_payload = {
                "format": "json",
                "prop": "extracts",
                "titles": random_title,
                "utf8": 1,
                "formatversion": "2",
                "exintro": 1,
                "explaintext": 1
            }

        while True:
            challenge_text = TextReadingChallenge.site.api('query', **api_payload)['query']['pages'][0]['extract']
            han = re.sub(r'[^\u4e00-\u9fff]', '', challenge_text)    # remove non han characters
            if len(han) > 10:
                break
        self.ans_index = random.randint(1, 10)
        self._ans = han[self.ans_index - 1]

        self._text = challenge_text[:50]

        cases = 6
        choices_index = random.sample(range(1, 10), cases)
        if self.ans_index not in choices_index:
            choices_index[cases // 2] = self.ans_index
        random.shuffle(choices_index)
        # Some bots just blindly click the first button
        if choices_index[0] == self.ans_index:
            choices_index[0], choices_index[cases // 2] = choices_index[cases // 2], choices_index[0]

        self._choices = [han[x - 1] for x in choices_index]

    def qus(self):
        return self.template.format(text=self._text, index=self.ans_index)

    def ans(self):
        return self._ans

    def choices(self):
        return self._choices
