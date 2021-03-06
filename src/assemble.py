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
from ase import Atoms
TEMPLATES = [
    'CALL zdr.index.chineseFulltextIndexSearch("IKAnalyzer", "{prop}:{value}", {num}) YIELD node as {node} with {node} ',  # fulltext search
    'match p=shortestpath((n1)-[rels*]-(n2)) ',  # match 2 nodes
    'match p=shortestpath((n1)-[rels1*]-(n2)-[rels2*]-(n3)) ',  # match 3 nodes
    '{conditions} ',  # where conditions
    'WITH [r IN rels | [STARTNODE(r), TYPE(r), ENDNODE(r)]] AS steps UNWIND steps AS step RETURN step;',  # return path
    'return {node}',  # return node
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
        self.sess = self.driver.session()

    def close(self):
        # Don't forget to close the driver connection when you are finished with it
        self.driver.close()

    def find_material(self, mname):
        with self.driver.session() as sess:
            result = sess.read_transaction(self._find_material, mname)
            for row in result:
                print("find person: {row}".format(row=row))

    def _search_query(self, query):
        result = self.sess.run(query)
        return [row for row in result]

    def search_query(self, query):
        result = self._search_query(query)
        for r in result:
            print('='*40)
            print(r[0][0].__dict__['_properties'], r[0][1], r[0][2].__dict__['_properties'])


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
            if pv[0] in FULLTEXT:  # ????????????????????????????????????zdr????????????
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
                        conditions += "{}.{} contains '{}' ".format(_n, pv[0], pv[1])
                    else:
                        conditions += '{}.{} = {} '.format(_n, pv[0], pv[1])
                else:
                    conditions += 'AND '
                    if pv[0] in CODES:
                        conditions += "{}.{} contains '{}' ".format(_n, pv[0], pv[1])
                    else:
                        conditions += '{}.{} = {} '.format(_n, pv[0], pv[1])
            FULL_TEXTS.append(fulltext)
        if conditions:
            CONDITIONS.append(conditions)
        # ????????????
        self.has_seen = set()

    def str_combine(self, prev_entity, prev_props, entities, wheres, no_e):
        # ??????????????????????????????????????????
        # ?????????????????????
        _str = 'n' + str(no_e) + ':{node} ' + '|@|' + '{prop_values} '
        # TODO ???????????????????????????
        _node = prev_entity[0]
        # ??????-??????
        _str_pv = ''
        # ??????
        _str_where = ''
        # ????????????
        for i, pv in enumerate(prev_props):

            # TODO ??????int??????????????????????????????
            if _node == 'Material' and pv[0] == 'mat_code':

                _str_pv += pv[0] + ':' + pv[1]

            # TODO ??????????????????
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
        # ????????????
        entities.append(_str)
        # ????????????
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
            # ????????????
            _p = r[0]
            _value = dicts_properties[_p]
            # ????????????
            current_entity = _value[-1]

            # ???????????????
            if not prev_entity:
                prev_entity = current_entity

            # ????????????-???
            prev_props.append(r)

            # ??????????????????
            if _p not in self.has_seen:
                self.has_seen.add(_p)
                if current_entity != prev_entity:
                    # ?????????????????????????????????
                    self.no_e += 1
                    # _ = self.str_combine(prev_entity, prev_props[:-1], entities, wheres, self.no_e)
                    self.str_combine2(prev_entity, prev_props[:-1], FULL_TEXTS, CONDITIONS, no_e=self.no_e)
                    # ????????????
                    prev_props = prev_props[-1]
                    prev_entity = current_entity
                    if not RES:
                        self.no_e += 1
                        # _ = self.str_combine(current_entity, [prev_props], entities, wheres, self.no_e)
                        self.str_combine2(prev_entity, [prev_props], FULL_TEXTS, CONDITIONS, no_e=self.no_e)

            else:
                if current_entity == prev_entity or set(prev_entity).issubset(set(current_entity)):
                    # ????????????????????????????????????????????????????????????????????????
                    self.no_e += 1
                    # _ = self.str_combine(prev_entity, prev_props[:-1], entities, wheres, self.no_e)
                    self.str_combine2(prev_entity, prev_props[:-1], FULL_TEXTS, CONDITIONS, no_e=self.no_e)
                    # ????????????
                    prev_props = prev_props[-1]
                    if not RES:
                        self.no_e += 1
                        # _ = self.str_combine(current_entity, [prev_props], entities, wheres, self.no_e)
                        self.str_combine2(prev_entity, [prev_props], FULL_TEXTS, CONDITIONS, no_e=self.no_e)
                    continue

            # if not RES:
            #     self.no_e += 1
            #     # _ = self.str_combine(current_entity, prev_props, entities, wheres, self.no_e)
            #     self.str_combine2(prev_entity, prev_props, FULL_TEXTS, CONDITIONS, no_e=self.no_e)

        RETURNS = TEMPLATES[4]

        # if self.no_e == 1:
        #     RETURNS = TEMPLATES[5].format(node='n' + str(self.no_e), num=self.num)
        if self.no_e == 2:
            MATCHES = TEMPLATES[1]
        #     RETURNS = TEMPLATES[4].format(','.join(['n' + str(i) for i in range(1, self.no_e + 1)]),
        #                                   num=self.num)

        elif self.no_e > 2:
            MATCHES = TEMPLATES[2]
        #     RETURNS = TEMPLATES[4].format(','.join(['n' + str(i) for i in range(1, self.no_e + 1)]),
        #                                   num=self.num)

        if CONDITIONS == []:
            CONDITIONS = ''
        else:
            CONDITIONS = 'where ' + TEMPLATES[3].format(conditions='AND '.join(CONDITIONS))
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
    query = "????????????||20725181JDW3 ????????????||?????????12???"
    print('query: ')
    print(query)
    print('========================')
    q = ass._assemble(query)
    ass.search_query(q)