#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A Hideo Kojima Fan
@author:dw
@time:2021/06/23
"""
import torch
import json
from pyhanlp import *
import numpy as np
from collections import defaultdict

a = torch.empty(10, 3, 32, 32)
a.stride()


# 实体对照表
dicts_nodes = {
    'BATCH': ['批次', 'batch'],
    'Material': ['wuliao', '物料', 'material', '物资'],
    'MRQ': ['物料需求', '物料需求单', '物资需求单'],
    'PR': ['采购需求', '采购需求单'],
    'BID': ['标书', '标段', '投标', '招标'],
    'Purchase': ['采购单', '订单', 'purchase', '购买', '采购'],
    'Ship': ['船运单', 'ship', '海运', '船单', '船运'],
    'Stock': ['地点', '仓库', '工厂', '地址', 'stock'],
    'Stock_Input': ['入库单', '入库'],
    'Stock_Output': ['出库单', '出库编码', '出库'],
    'Transport': ['转运', '转储单', '转储', '转移', '运输', 'transport'],
}

WORDS = set()
dicts_rev_nodes = {}
for k, v in dicts_nodes.items():
    for kk in v:
        dicts_rev_nodes[kk] = k
        WORDS.add(kk)

# 实体属性
dicts_properties = {
    'mat_desc': ['物料描述', '物资描述', '物料长描述',['Material']],
    'affiliated_company': ['关联公司', '附属公司', ['Ship']],
    'approval_status': ['审核状态', '批准进度', ['MRQ', 'PR']],
    'arrival_date': ['预计到达时间', '到达时间', '到达日期', ['PR']],
    'batch_code': ['批次编码', '批次编码', '批次单编码', '批次单据', ['BATCH']],
    'bid_amount': ['投标金额', '标书金额', ['BID']],
    'bid_code': ['标段编码', '招标编码', '标书编码', '投标编码', '投标码', '招标码', ['BID']],
    'bid_end_date': ['竞标截止日期', '投标截止日期', '标书截止日期', ['BID']],
    'bid_num': ['招标号', '竞标号', '投标号', ['BID']],
    'bid_start_date': ['竞标开始日期', '投标开始日期', '标书开始日期', '竞标起始日期', '投标起始日期', '标书起始日期', ['BID']],
    'bid_supplier': ['投标供应商', '供应商', '竞标供应商', '招标供应商', ['BID']],
    'can_dqty': ['可以送达数量', '可配送数量', '配送数量', ['Purchase']],
    'evaluation_start_date': ['评估开始日期', '预计开始日期', '计划开始日期', ['BID']],
    'evaluation_end_date': ['评估截止日期', '预计截止日期', '计划截止日期', '评估结束日期', '预计结束日期', '计划结束日期', ['BID']],
    'clarify_start_date': ['证实开始日期', '实际开始日期', '验证开始日期', ['BID']],
    'clarify_end_date': ['证实截止日期', '实际截止日期', '验证截止日期', '证实结束日期', '实际结束日期', '验证结束日期', ['BID']],
    'creation_time': ['创建时间', ['Purchase', 'BID', 'PR', 'Contract']],
    'contract_code': ['合同编码', ['Contract']],
    'contract_creator': ['合同创建者', ['Contract']],
    'contract_no': ['合同号', ['Contract']],
    'crane_type': ['起重机样式', '起重机型号', ['Ship']],
    'demand_cause': ['需求原因', '提报原因', ['MRQ']],
    'demand_time': ['需求时间', ['MRQ']],
    'doc_date': ['记录时间', '登记时间', ['Stock_Input', 'Stock_Output', 'Transport']],
    'dqty': ['需求数量', ['Stock_Input', 'Stock_Output']],
    'facility': ['设备', '功能位置', ['MRQ']],
    'founder': ['申请创始人', '创建者', '申请创建者', '创始人', ['PR']],
    'fty_code': ['工厂编码', '工厂', ['Stock']],
    'header_text': ['头文本', '头描述', ['PR']],
    'input_qty': ['运入数量', '存入数量', '存储数量', '入库数量', ['Transport']],
    'irqty': ['检验数量', '记录数量', ['Stock_Input']],
    'load_qty': ['装载数量', '运出数量', '出库数量', ['Stock_Output']],
    'location_code': ['地点编码', '地址编码', '存储点', ['Stock']],
    'mat_code': ['物料编码', '货物编码', '物资编码', ['Material']],
    'mat_doc_year': ['物料记录年份', '货物记录年份', '物资记录年份', ['Material']],
    'mat_group': ['物料组', '物料分组', '物料组别', ['Material']],
    'mat_name': ['物料名', '物料名称', ['Material']],
    'mat_type': ['物料类型', '物料分类', '物料类别', ['Ship']],
    'move_code': ['运输编号', '行动编号', '移动编号', ['Transport']],
    'mrq_code': ['需求提报编号', '物料需求编号', ['MRQ']],
    'mrq_name': ['需求提报名称', '物料需求名称', ['MRQ']],
    'notice_creation_time': ['公告创建时间', ['BID']],
    'planned_deliver_time': ['计划交付时间', ['Purchase']],
    'planned_use_time': ['计划使用时间', ['MRQ']],
    'pr_code': ['采购需求编码', '采购需求单号', ['PR']],
    'pr_type': ['采购需求类型', ['MRQ']],
    'pre_receipt_type': ['预接收类型', '拟收货类型', ['Stock_Input']],
    'price': ['价格', '价值', '付款', '价钱', ['Purchase']],
    'proqty': ['生产接受数量', '生产数量', ['Stock_Input']],
    'prqty': ['采购需求量', ['Stock_Input', 'Purchase']],
    'psubqty': ['采购提交数量', '购买提交数据量', ['Purchase']],
    'purchase_code': ['采购编码', ['Purchase']],
    'purchase_creation_time': ['采购单创建时间', '采购创建时间', ['Purchase']],
    'purchase_group_code': ['采购组编码', ['Purchase']],
    'purchase_type': ['采购类型', ['Purchase']],
    'qty': ['运输数量', '数量', ['MRQ', 'PR', 'Transport']],
    'receipt_type': ['接收类型', ['Stock_Input']],
    'reserve_time': ['预定时间', '保留时间', '储存时间', '滞留时间', ['Stock_Output']],
    'saleqty': ['销量', '销售数量', ['Purchase']],
    'scode': ['库存编码', ['Stock']],
    'sendqty': ['发货量', '送出量', ['Purchase']],
    'stock_input_code': ['库存进货单号', '库存入库单号', ['Stock_Input']],
    'stock_output_code': ['库存出货单号', '库存出库单号', ['Stock_Output']],
    'supplier_name': ['供应商名称', '供应商', ['Purchase']],
    'total_amount': ['总量', '总数量', ['PR', 'Purchase']],
    'transport_code': ['转运编号', '运输编号', '运输单号', ['Transport']],
    'unit': ['单位', ['PR', 'Purchase']],
    'unit_name': ['单位名称', ['Purchase']],
    'unload_qty': ['卸载量', '卸货量', ['Transport']],
    'voyage_no': ['船运编号', '海运编号', ['Ship']],
    'wh_code': ['仓库编码', ['Stock']],
    'wh_sys': ['仓库系统', ['Stock']],
    'winning_end_date': ['中标截止日期', '中标结束日期', ['BID']],
    'winning_start_date': ['中标起始日期', '中标开始日期', ['BID']]
}


dicts_nodes_has_words = defaultdict(set)
dicts_props_has_words = defaultdict(set)
dicts_rev_props = {}
dicts_rev_belong = {}
for k, v in dicts_properties.items():
    words_list = []
    for kk in v:
        if not isinstance(kk, list):
            words = HanLP.segment(kk)
            for w in words:
                words_list.append(w.word)
                dicts_rev_props[w.word] = k

    for w in words_list:
        WORDS.add(w)
        dicts_props_has_words[k].add(w)
        dicts_rev_belong[w] = v[-1]
        for n in v[-1]:
            dicts_nodes_has_words[n].add(w)

# print(dicts_rev_props)
# print('=' * 30)
# print(dicts_rev_belong)
# print('=' * 30)
print(dicts_nodes_has_words)
print('=' * 30)
print(dicts_props_has_words)


# 关系对照表
dicts_preds = [
    ['参考', '查找', '基于', '依赖', '参照', '需要', '需求'],  # 0
    ['入库', '进入', '存入', '存放', '转入', '运入', '存储'],  # 1
    ['出库', '转出', '送出', '出', '运出'],  # 2
    ['包含', '使用', '需要', '需求'],  # 3
    ['包含', '需求', '需要', '转出', '运出']  # 4
]


# 三元组
dicts_edges = {
    'batch_in': ['BATCH', 0, 'Stock_Input'],  # 单据之间
    'batch_out': ['BATCH', 0, 'Stock_Output'],  # 单据之间
    'batch_transport': ['BATCH', 0, 'Transport'],  # 单据之间
    'in_stock': ['Transport', 1, 'Stock'],
    'out_stock': ['Transport', 2, 'Stock'],
    'out_mat': ['Transport', 4, 'Material'],
    'lookup': ['Purchase', 0, 'Stock_Input'],  # 单据之间
    'required': ['Material', 3, 'BATCH'],
    'ship': ['Transport', 0, 'Ship']  # 单据之间
}

word2id = {k: i for i, k in enumerate(WORDS)}
id2word = {i: k for i, k in enumerate(WORDS)}
key2id = {k: i for i, k in enumerate(dicts_props_has_words)}
id2key = {i: k for i, k in enumerate(dicts_props_has_words)}

NUM_WORDS = len(WORDS)
props_embedding = {}
for k, v in dicts_props_has_words.items():
    init_row = np.zeros(NUM_WORDS)
    for vv in v:
        row = np.zeros(NUM_WORDS)
        row[word2id[vv]] = 1
        init_row += row
    props_embedding[k] = init_row.tolist()

# print(props_embedding['affiliated_company'])

with open('../data/props_embedding.json', 'w') as f:
    json.dump(props_embedding, f)

with open('../data/words_dicts.json', 'w') as f:
    json.dump(word2id, f)


def combine():
    pass


if __name__ == '__main__':
    pass
