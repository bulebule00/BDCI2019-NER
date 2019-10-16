import codecs
import csv
import re
from tqdm import tqdm
import pandas as pd
import random
import os
import json
import uuid


def read_csv():
    train_df = pd.read_csv('./data/Train_Data.csv')
    train_df['text'] = train_df['title'].fillna('') + '。' + train_df['text'].fillna('')

    test_df = pd.read_csv('./data/Test_Data.csv')
    test_df['text'] = test_df['title'].fillna('') + '。' + test_df['text'].fillna('')
    return train_df, test_df


def get_sentences(text, max_length=128):
    # if len(text) <= max_length - 2:
    #     return [text]
    tmp = re.split('(。|！|？|；|，|\?|\!)', text)
    sent = ''
    sentences = []
    if tmp[-1] != '':
        tmp.append('。')
    else:
        tmp = tmp[:-1]

    i = 0
    while i < len(tmp) - 1:

        if len(sent + tmp[i] + tmp[i + 1]) > max_length - 2 and len(tmp[i]) <= 150:
            sentences.append(sent)
            sent = ''
        if tmp[i] != '' and len(tmp[i]) <= 150:
            sent += (tmp[i] + tmp[i + 1])
        i += 2
    if sent != '':
        sentences.append(sent)

    return sentences


def gen_json():
    train_df, test_df = read_csv()
    additional_chars = set()
    for t in list(test_df.text) + list(train_df.text):
        additional_chars.update(re.findall(u'[^\u4e00-\u9fa5a-zA-Z0-9\*]', t))

    extra_chars = set("!#$%&\()*+,-./:;<=>?@[\\]^_`{|}~！#￥%&？《》{}“”，：‘’。（）·、；【】")
    additional_chars = additional_chars.difference(extra_chars)

    def remove_additional_chars(input):
        for x in additional_chars:
            input = input.replace(x, "")
        return input

    train_df["text"] = train_df["text"].apply(remove_additional_chars)
    test_df["text"] = test_df["text"].apply(remove_additional_chars)

    # gen train
    print("generate train...")
    rows = [each for each in train_df.iloc[:].itertuples()]
    with codecs.open('./data/train.txt', 'w') as up:
        for row in tqdm(rows):
            sentences = get_sentences(row.text)
            up.write('Ж{0}Ж {1}\n'.format(str(row.id), 'O'))
            for i, sent in enumerate(sentences):
                for entity in bio_dictionary:
                    sent = sent.replace(entity, 'Ё' + (len(entity) - 1) * 'Ж')
                for c1, c2 in zip(sent, sentences[i]):
                    if c1 == 'Ё':
                        up.write('{0} {1}\n'.format(c2, 'B-ORG'))
                    elif c1 == 'Ж':
                        up.write('{0} {1}\n'.format(c2, 'I-ORG'))
                    else:
                        up.write('{0} {1}\n'.format(c2, 'O'))

                up.write('\n')

    # gen dev
    print("generate dev...")
    with codecs.open('./data/dev.txt', 'w') as up:
        rows = random.sample([each for each in train_df.iloc[:].itertuples()], 100)
        for row in tqdm(rows):
            sentences = get_sentences(row.text)
            up.write('Ж{0}Ж {1}\n'.format(str(row.id), 'O'))
            for i, sent in enumerate(sentences):
                if len(sent) < 2:
                    continue
                for entity in bio_dictionary:
                    sent = sent.replace(entity, 'Ё' + (len(entity) - 1) * 'Ж')

                for c1, c2 in zip(sent, sentences[i]):
                    if c1 == 'Ё':
                        up.write('{0} {1}\n'.format(c2, 'B-ORG'))
                    elif c1 == 'Ж':
                        up.write('{0} {1}\n'.format(c2, 'I-ORG'))
                    else:
                        up.write('{0} {1}\n'.format(c2, 'O'))
                up.write('\n')

    # gen test
    print("generate test...")
    with codecs.open('./data/test.txt', 'w') as up:
        rows = [each for each in test_df.iloc[:].itertuples()]
        for row in tqdm(rows):
            sentences = get_sentences(row.text)
            up.write('Ж{0}Ж {1}\n'.format(str(row.id), 'O'))
            for sent in sentences:
                for c1 in sent:
                    up.write('{0} {1}\n'.format(c1, 'O'))
                up.write('\n')


def judge_pure_english(keyword):
    return all(ord(c) < 128 for c in keyword)


def gen_csv(mode='test'):
    predict = codecs.open('./ner_output/label_%s.txt' % mode).read().split('\n\n')
    save_name = './res/%s.csv' % mode
    if os.path.exists(save_name):
        os.remove(save_name)
    res = codecs.open(save_name, 'w')
    res.write('id,unknownEntities\n')
    id = ''
    unknown_entities = set()
    for sent in tqdm(predict):
        sent = sent.split('\n')
        entity = ''
        for each in sent:
            if each == '':
                continue
            tmp_id = re.findall('Ж(.*?)Ж', each)
            if len(tmp_id) == 1:
                if id != '':
                    # unknown_entities = select_candidates(unknown_entities)
                    res.write('{0},{1}\n'.format(id, ';'.join(list(unknown_entities))))
                id = tmp_id[0]
                unknown_entities = set()
                continue
            word, _, tag = each.split()
            if tag == 'B-ORG':
                if entity == '':
                    entity = word
                else:
                    entity = filter_word(entity)
                    if entity != '':
                        unknown_entities.add(entity)
                    entity = ''
            elif tag == 'I-ORG':
                if entity != '':
                    entity += word
            else:
                entity = filter_word(entity)
                if entity != '':
                    unknown_entities.add(entity)
                entity = ''
    # unknown_entities = select_candidates(unknown_entities)
    res.write('{0},{1}\n'.format(id, ';'.join(list(unknown_entities))))
    res.close()


def pre_process():
    print('process train.csv...')
    with open('./data/old/Train_Data_Hand.csv', 'r', encoding='utf-8') as myFile:
        lines = list(csv.reader(myFile))
        data = []
        for line in lines[1:]:
            line = clean(line)
            data.append(line)

        headers = ['id', 'title', 'text', 'unknownEntities']
        with open('./data/Train_Data.csv', 'w', encoding='utf-8') as f:
            f_csv = csv.writer(f)
            f_csv.writerow(headers)
            f_csv.writerows(data)

    print('process test.csv...')
    with open('./data/old/Test_Data.csv', 'r', encoding='utf-8') as myFile:
        lines = list(csv.reader(myFile))
        data = []
        for line in lines[1:]:
            line = clean(line)
            data.append(line)
        headers = ['id', 'title', 'text']
        with open('./data/Test_Data.csv', 'w', encoding='utf-8') as f:
            f_csv = csv.writer(f)
            f_csv.writerow(headers)
            f_csv.writerows(data)


def clean(line):
    # remove title is the same as text
    if len(line[1]) > 40 and line[2].startswith(line[1][:-9]):
        line[1] = ''
    print(len(line[1]))
    for i in range(1, 3):
        if line[i] != '':
            line[i] = line[i].replace(",", "，")
            line[i] = line[i].replace("\xa0", "")
            line[i] = line[i].replace("\b", "")
            line[i] = line[i].replace('"', "")
            line[i] = re.sub("\t|\n|\x0b|\x1c|\x1d|\x1e", "", line[i])
            line[i] = line[i].strip()
            line[i] = re.sub('\?\?+', '', line[i])
            line[i] = re.sub('\{IMG:.?.?.?\}', '', line[i])
            line[i] = re.sub('\t|\n', '', line[i])
            line[i] = re.sub('\<.*?\>', '', line[i])
    return line


if __name__ == "__main__":
    # pre_process()
    gen_json()
    # gen_csv(mode='test')
