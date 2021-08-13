#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A Hideo Kojima Fan
@author:dw
@time:2021/07/02
"""
import re


dates = '[0-9]{4}-[0-9]{2}-[0-9]{2}T?[0-9]{0,2}:?[0-9]{0,2}:?[0-9]{0,2}'

REGXS = {
    'batch_code': re.compile('(?<![0-9])2[0-9]{7,}'),
    'pr_code': re.compile('(?<![0-9])[13-9][0-9]{7,}'),
    'bid_num': re.compile('[1-2][0-9]+.+0[1-9](?![0-9])|[A-Z]+.+0[1-9](?![0-9])'),
    'bid_start_date': re.compile(dates),
    'bid_end_date': re.compile(dates),
    'clarify_start_date': re.compile(dates),
    'clarify_end_date': re.compile(dates),
    'evaluation_start_date': re.compile(dates),
    'evaluation_end_date': re.compile(dates),
    'winning_start_date': re.compile(dates),
    'winning_end_date': re.compile(dates),
    'bid_supplier': re.compile('[\u4e00-\u9fa5]+.+[\u4e00-\u9fa5]'),
    'bid_amount': re.compile(r'(?<![0-9a-zA-Z])[0-9]+\.*[0-9]+(?![0-9A-Za-z])'),
    'notice_creation_time': re.compile(dates),
    'notice_creation_person': re.compile('[\u4e00-\u9fa5]+'),
    'contract_no': re.compile('[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+-[A-Za-z0-9]+'),
    'bid_code': re.compile('[1-2][0-9]+.+0[1-9](?![0-9])|[A-Z]+.+0[1-9](?![0-9])'),
    'contract_creator': re.compile('[\u4e00-\u9fa5]+'),
    'creation_time': re.compile(dates),
    'contract_code': re.compile(r'(?<![A-Z])CCL[0-9]+\w+(?![0-9A-Z])'),
    'mat_code': re.compile(r'[0-9]{8}'),
    'mat_name': re.compile('i18n_[0-9]+_mid'),
    'mat_group': re.compile('(?<![A-Z])A[0-9]{6}(?![0-9])'),
    'mrq_code': re.compile('9[0-9]+(?![0-9])'),
    'facility': re.compile('(?<![A-Z])[A-Z]{2,}[0-9]*-[A-Z0-9]+(?![A-Z0-9])'),
    'mrq_name': re.compile('[\u4e00-\u9fa5]{2}_\w+_\w+_\w+(?![\u4e00-\u9fa5])'),
    'pr_type': re.compile('[A-Z]{4,}'),
    'demand_time': re.compile(dates),
    'approval_status': re.compile('[A-Z]{4,}'),
    'planned_use_time': re.compile(dates),
    'mat_desc': re.compile('.*')
    # demand_cause

}


if __name__ == '__main__':
    # sent = '23423401'
    # sent = 'pr num为18-CNOOC-HW-YQ-049901'
    # sent = '2003-xiongchao-20190214-00801'
    sent1 = 'LGR1805601sdfdsf 2019-12-21 青岛太平洋海洋工程（深圳）有限公司 123.56 48f317e3-967a-4462-ae45-ba2ab44fb1d9'
    print(re.findall(REGXS['bid_num'], sent1))
    sent2 = re.sub(REGXS['bid_num'], '', sent1)
    print(re.findall(REGXS['bid_start_date'], sent2))
    sent2 = re.sub(REGXS['bid_start_date'], '', sent2)
    print(re.findall(REGXS['bid_supplier'], sent2))
    print(re.findall(REGXS['bid_amount'], sent2))
    print(re.findall(REGXS['contract_no'], sent2))