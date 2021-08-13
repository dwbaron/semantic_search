#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A Hideo Kojima Fan
@author:dw
@time:2021/07/08
"""
import re
from pyhanlp import *
import numpy as np
import json
from src.dicts import word2id, dicts_properties
from src.regxs import REGXS


class Parser():
    def __init__(self, sep1=' ', sep2='||'):
        self.sep1 = sep1
        self.sep2 = sep2
        with open('../data/words_dicts.json', 'r') as f:
            self.dicts = json.load(f)  # words dict
        with open('../data/props_embedding.json', 'r') as f:
            self.embeddings = json.load(f)
        self.num_words = len(self.dicts)
        props = self.embeddings.keys()
        id2props = {i: p for i, p in enumerate(props)}
        self.id2props = id2props  # props row id
        em = []
        for _, v in self.embeddings.items():
            em.append(v)
        self.em = np.array(em)  # words embeddings

    def parse(self, query):
        segs = query.split(self.sep1)
        PROPS = []
        for seg in segs:
            pro, value = seg.split(self.sep2)
            words = HanLP.segment(pro)
            words_embedding = np.zeros(self.num_words)
            for w in words:
                if w.word in self.dicts:
                    words_embedding[self.dicts[w.word]] = 1

            cosine = np.dot(self.em, words_embedding)   # number props
            prop = self.id2props[cosine.argmax()]

            try:
                _value = re.search(REGXS[prop], value).group(0)  # value regex
            except AttributeError:
                _value = value

            PROPS.append([prop, _value])
        return PROPS


if __name__ == '__main__':
    query = '物料编码包含||20000032大概这样 物料名称哈哈||i18n_0000201673_mid 物料描述||12345上山打老虎'
    P = Parser()
    RES = P.parse(query)
    print(RES)