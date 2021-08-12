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


class Assemble:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

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


if __name__ == "__main__":
    bolt_url = "bolt://localhost:7687"
    user = "neo4j"
    password = "7612"
    app = Assemble(bolt_url, user, password)
    app.find_material(20007945)
    app.close()