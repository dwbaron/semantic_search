#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A Hideo Kojima Fan
@author:dw
@time:2021/08/05
"""


from neo4j import GraphDatabase
import logging
from neo4j.exceptions import ServiceUnavailable
from src.match import Parser
from src.dicts import dicts_properties, FULLTEXT, CODES
import re


TEMPLATES = [
    'CALL zdr.index.chineseFulltextIndexSearch("IKAnalyzer", "{prop}:{value}", {num}) YIELD node as {node} with {node} ',  # fulltext search
    'match p=(n1)-[*2..5]-(n2) ',  # match 2 nodes
    'match p=(n1)-[*2..5]-(n2)-[*2..5]-(n3) ',  # match 3 nodes
    'where {conditions} ',  # where conditions
    'return p limit {num}',  # return path
    'return {node} limit {num}',  # return node
    '{fulltext}{matches}{conditions}{returns}'  # full query
]


class Assemble:
    def __init__(self, uri, user, password, parser):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.parser = parser
        self.has_seen = set()
        self.entities = []
        self.wheres = []
        self.no_e = 0  # number of entities
        self.num = 10

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()

    def find_material(self, mname):
        with self.driver.session() as sess:
            result = sess.read_transaction(self._find_material, mname)
            for row in result:
                print("find person: {row}".format(row=row))

    @staticmethod
    def _find_material(tx, mname):
        query = (
            "match (n:Material) where n.mat_code=$mname "
            "return n"
        )
        result = tx.run(query, mname=mname)
        return [row for row in result]

    def str_combine2(self, prev_entity, prev_props, FULL_TEXTS, CONDITIONS, no_e, num=10):
        _node = prev_entity[0]
        fulltext = ''
        conditions = ''
        for i, pv in enumerate(prev_props):
            if pv[0] in FULLTEXT:  # 该属性存在长文本，需要用zdr模糊匹配
                fulltext = TEMPLATES[0].format(
                    prop=pv[0],
                    value=pv[1],
                    num=num,
                    node='n' + str(no_e)
                )
            else:
                _n = 'n' + str(no_e)
                if not conditions:
                    if pv[0] in CODES:
                        conditions += '{}.{} contains {} '.format(_n, pv[0], pv[1])
                    else:
                        conditions += '{}.{} = {} '.format(_n, pv[0], pv[1])
                else:
                    conditions += 'AND '
                    if pv[0] in CODES:
                        conditions += '{}.{} contains {} '.format(_n, pv[0], pv[1])
                    else:
                        conditions += '{}.{} = {} '.format(_n, pv[0], pv[1])
            FULL_TEXTS.append(fulltext)
        CONDITIONS.append(conditions)
        # 重置状态
        self.has_seen = set()

    def str_combine(self, prev_entity, prev_props, entities, wheres, no_e):
        # 遇到重复属性说明实体发生变换
        # 一个节点的拼装
        _str = 'n' + str(no_e) + ':{node} ' + '|@|' + '{prop_values} '
        # TODO 暂时不考虑多个实体
        _node = prev_entity[0]
        # 属性-值对
        _str_pv = ''
        # 条件
        _str_where = ''
        # 属性拼装
        for i, pv in enumerate(prev_props):

            # TODO 遇到int类型的属性值特殊处理
            if _node == 'Material' and pv[0] == 'mat_code':

                _str_pv += pv[0] + ':' + pv[1]

            # TODO 文本模糊匹配
            elif pv[0] in ['affiliated_company', 'header_text', 'founder',
                           'contract_creator', 'bid_supplier', 'mat_desc']:
                _str_where = "where {}.{} contains '{}' ".format('n' + str(no_e), pv[0], pv[1])
                wheres.append(_str_where)
                if i == len(prev_props) - 1:
                    _str_pv = re.sub(', $', '', _str_pv)
            else:
                _str_pv += pv[0] + ':' + "'" + pv[1] + "'"

            if i < len(prev_props) - 1:
                _str_pv += ', '

        _str = _str.format(node=_node, prop_values=_str_pv)
        _str = _str.replace('|@|', '{')
        _str += '}'
        # 添加节点
        entities.append(_str)
        # 重置状态
        self.has_seen = set()
        return []

    def _assemble(self, query):
        RES = self.parser.parse(query)
        prev_entity = None
        prev_props = []
        # wheres = []
        # entities = []
        FULL_TEXTS = []
        CONDITIONS = []
        MATCHES = ''

        while RES:
            r = RES.pop(0)
            # 当前属性
            _p = r[0]

            _value = dicts_properties[_p]
            # 当前实体
            current_entity = _value[-1]

            # 第一个实体
            if not prev_entity:
                prev_entity = current_entity

            # 添加属性-值
            prev_props.append(r)

            # 并非重复属性
            if _p not in self.has_seen:
                self.has_seen.add(_p)

            else:
                # 同一类实体但是属性名称重复，说明是另一个同类实体
                self.no_e += 1
                if current_entity == prev_entity or set(prev_entity).issubset(set(current_entity)):
                    # _ = self.str_combine(prev_entity, prev_props[:-1], entities, wheres, self.no_e)
                    self.str_combine2(prev_entity, prev_props[:-1], FULL_TEXTS, CONDITIONS, no_e=self.no_e)
                    # 重置状态
                    prev_props = prev_props[-1]
                    if not RES:
                        self.no_e += 1
                        # _ = self.str_combine(current_entity, [prev_props], entities, wheres, self.no_e)
                        self.str_combine2(prev_entity, [prev_props], FULL_TEXTS, CONDITIONS, no_e=self.no_e)
                    continue
                else:
                    # 非同一实体，则触发拼接
                    self.no_e += 1
                    # _ = self.str_combine(prev_entity, prev_props[:-1], entities, wheres, self.no_e)
                    self.str_combine2(prev_entity, prev_props[:-1], FULL_TEXTS, CONDITIONS, no_e=self.no_e)
                    # 重置状态
                    prev_props = prev_props[-1]
                    prev_entity = current_entity
                    if not RES:
                        self.no_e += 1
                        # _ = self.str_combine(current_entity, [prev_props], entities, wheres, self.no_e)
                        self.str_combine2(prev_entity, [prev_props], FULL_TEXTS, CONDITIONS, no_e=self.no_e)
                    continue
            if not RES:
                self.no_e += 1
                # _ = self.str_combine(current_entity, prev_props, entities, wheres, self.no_e)
                self.str_combine2(prev_entity, prev_props, FULL_TEXTS, CONDITIONS, no_e=self.no_e)

        if self.no_e == 1:
            RETURNS = TEMPLATES[5].format(node='n' + str(self.no_e), num=self.num)
        elif self.no_e == 2:
            RETURNS = TEMPLATES[4].format(num=self.num)
            MATCHES = TEMPLATES[1]
        else:
            RETURNS = TEMPLATES[4].format(num=self.num)
            MATCHES = TEMPLATES[2]

        CONDITIONS = TEMPLATES[3].format(conditions='AND '.join(CONDITIONS))
        # print(entities)
        # print(wheres)
        full_query = TEMPLATES[-1].format(
            fulltext=' '.join(FULL_TEXTS),
            matches=''.join(MATCHES),
            conditions=CONDITIONS,
            returns=RETURNS
        )

        print(full_query)

        return full_query


if __name__ == "__main__":
    bolt_url = "bolt://10.60.11.143:7687"
    user = "neo4j"
    password = "7612"
    # app = Assemble(bolt_url, user, password)
    # app.find_material(20007945)
    # app.close()

    pas = Parser()
    ass = Assemble(bolt_url, user, password, pas)
    query = "物料编码包含||20000032大概这样 物料名称哈哈||i18n_0000201673_mid 物料描述||12345上山打老虎"
    print('query: ')
    print(query)
    print('========================')
    ass._assemble(query)