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
from src.dicts import dicts_properties
import re


TEMPLATES = [
    "match n=({node1}) {where} {returns}",
    "match p=({node1})-[*2..4]-({node2})-[*2..4]-({node3})-[*2..4]-({node4}) {where} {returns}",
    "match p=({node1})-[*2..4]-({node2})-[*2..4]-({node3}) {where} {returns}",
    "match p=({node1})-[*1..4]-({node2}) {where} {returns}"
]


class Assemble:
    def __init__(self, uri, user, password, parser):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.parser = parser
        self.has_seen = set()
        self.entities = []
        self.wheres = []
        self.no_e = 0  # number of entities

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
        entities = []
        prev_entity = None
        prev_props = []
        wheres = []
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
                    _ = self.str_combine(prev_entity, prev_props[:-1], entities, wheres, self.no_e)
                    # 重置状态
                    prev_props = prev_props[-1]
                    if not RES:
                        self.no_e += 1
                        _ = self.str_combine(current_entity, [prev_props], entities, wheres, self.no_e)
                    continue
                else:
                    # 非同一实体，则触发拼接
                    self.no_e += 1
                    _ = self.str_combine(prev_entity, prev_props[:-1], entities, wheres, self.no_e)
                    # 重置状态
                    prev_props = prev_props[-1]
                    prev_entity = current_entity
                    if not RES:
                        self.no_e += 1
                        _ = self.str_combine(current_entity, [prev_props], entities, wheres, self.no_e)
                    continue
            if not RES:
                self.no_e += 1
                _ = self.str_combine(current_entity, prev_props, entities, wheres, self.no_e)

        # print(entities)
        # print(wheres)
        return entities, wheres

    def assemble(self, query):
        cypher_str = ''
        self.entities, self.wheres = self._assemble(query)
        if len(self.entities) == 1:
            cypher_str = TEMPLATES[0].format(node1=self.entities[0], where=self.wheres[0], returns='return p limit 5')

        elif len(self.entities) == 2:
            cypher_str = TEMPLATES[3].format(node1=self.entities[0], node2=self.entities[1],
                                             where=self.wheres[0], returns='return p limit 5')

        print(cypher_str)


if __name__ == "__main__":
    bolt_url = "bolt://10.60.11.143:7687"
    user = "neo4j"
    password = "7612"
    # app = Assemble(bolt_url, user, password)
    # app.find_material(20007945)
    # app.close()

    pas = Parser()
    ass = Assemble(bolt_url, user, password, pas)
    query = "物料编码包含||20000032大概这样 物料名称哈哈||i18n_0000201673_mid 物料描述||12345上山打老虎 物料编码哈哈||20000031"
    print('query: ')
    print(query)
    print('========================')
    ass.assemble(query)