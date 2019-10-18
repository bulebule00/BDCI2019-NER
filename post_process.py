import codecs
import csv
import re

predict_dictionary = open('./data/dict/dict_oracle.txt').read().split('\n')
predict_dictionary = [each.strip() for each in predict_dictionary]
predict_dictionary = set([each for each in predict_dictionary if each != ''])

remove = set(open('./data/dict/remove.txt').read().split('\n'))
if '' in remove: remove.remove('')


# def select_candidates(unknown_entities):
#     unknown_entities = list(unknown_entities)
#     tmp = sorted(unknown_entities, key=lambda e: len(e))
#     if tmp != []:
#         unknown_entities = []
#         for i in range(len(tmp) - 1):
#             flag = True
#             for j in range(i + 1, len(tmp)):
#                 if tmp[i] in tmp[j]:
#                     flag = False
#                     break
#             if flag:
#                 unknown_entities.append(tmp[i])
#         unknown_entities.append(tmp[-1])
#     return unknown_entities

def judge_pure_english(keyword):
    return all(ord(c) < 128 for c in keyword)


def post_process(mode='test'):
    print('Post process...')
    # results = open('./res/ner_%s.csv' % mode).read().split('\n')
    results = open('./res/best.csv').read().split('\n')
    if results[-1] == '':
        results = results[:-1]
    res = codecs.open('./res/ner_post_%s.csv' % mode, 'w')
    # res = codecs.open('./res/best.csv', 'w')

    res.write('id,unknownEntities\n')

    with open('./data/old/T%s_Data.csv' % mode[1:], 'r', encoding='utf-8') as myFile:
        lines = list(csv.reader(myFile))
        if lines[-1] == '':
            lines = lines[:-1]
        for i in range(1, len(lines)):
            id, candidates = results[i].split(',')
            candidates = candidates.split(';')
            entity = completion(candidates, lines[i])
            res.write('{0},{1}\n'.format(id, ';'.join(entity)))
    res.close()


def completion(candidates, context):
    remove_char = {']', '：', '~', '！', '%', '[', '《', '】', ';', ':', '》', '？', '>', '/', '#', '。', '；', '&', '=',
                   '，',
                   '【', '@', '、', '|', ',', '”', '?'}

    context = context[1] + '。' + context[2]
    tmp = []
    for each in candidates:
        index = context.find(each)
        ex = 1
        if context.count(each) > 1:
            for i in range(1, len(context) - index - len(each)):
                if context.count(each) != context.count(context[index:index + i + len(each)]):
                    ex = i
                    break

            new = context[index:index + ex - 1 + len(each)]
            flag = True
            if len(new) < 22 and len(re.findall("\\" + "|\\".join(remove_char), new)) == 0:
                try:
                    xx = re.findall('(%s.*?)(理财|集团|控股|平台|银行|公司|资本|投资|生态|策略|控股集团)' % each, new)
                    if xx:
                        flag = False
                        new = xx[0][0] + xx[0][1]
                        if context.count(each) == context.count(new):
                            tmp.append(new)
                        else:
                            tmp.append(each)
                            tmp.append(new)
                    else:
                        if ex > 1:
                            if len(each) <= 3 and len(new) == 4:
                                tmp.append(new)
                                # print(each, new)

                            flag = False
                except:
                    pass

            if flag:
                tmp.append(each)
        else:
            tmp.append(each)

    tmp = list(set(tmp))

    xx = []
    for w in tmp:
        if w in remove:
            continue
        cnt = context.count(w)
        # if judge_pure_english(w) and cnt == 1:
        #     continue
        xx.append((cnt, len(context) - context.find(w), w))
    xx.sort(key=lambda k: (k[0], k[1]), reverse=True)

    res = []
    for i in range(len(xx) - 1):
        if xx[i + 1][0] == xx[i][0] and xx[i + 1][2].startswith(xx[i][2]):
            continue
        res.append(xx[i])
    if len(xx) > 0:
        res.append(xx[-1])

    res = [each[2] for each in res]
    # if len(res) <= 2:
    #     return [each[2] for each in res]
    # else:
    #     tmp = [each[2] for each in res[:2]]
    #     for i in range(2, len(res)):
    #         if res[i][0] >= 2 and (len(context) - res[i][1]) < len(context) // 2:
    #             tmp.append(res[i][2])
    #     return tmp
    return res


def remove_entity(mode='test'):
    print('Removing entities...')
    results = open('./res/ner_post_%s.csv' % mode).read().split('\n')
    if results[-1] == '':
        results = results[:-1]
    res = codecs.open('./res/ner_post_%s.csv' % mode, 'w')
    res.write('id,unknownEntities\n')
    for line in results[1:]:
        if ',' in line:
            id, entities = line.split(',')
            entities = entities.split(';')
            tmp = []
            for each in entities:
                if each in predict_dictionary:
                    continue
                tmp.append(each)
            res.write('%s,%s\n' % (id, ';'.join(tmp)))
        else:
            res.write('%s\n' % line)

    lines = open('./res/ner_%s.csv' % mode, encoding='utf-8').read().split('\n')
    tmp = []
    for i in range(1, len(lines)):
        entities = ''
        if ',' in lines[i]:
            id, entities = lines[i].split(',')
        else:
            id = lines[i]
        entities = entities.split(';')
        tmp.extend(entities)

    tmp = list(set(tmp))
    tmp.sort(key=lambda k: (k, len(k)))
    # C = list(Counter(tmp).items())
    # C.sort(key=lambda k: k[1], reverse=True)
    # cnt = 0
    # for each in C:
    #     if each[0] != '':
    #         xx.append(each[0] + ' ' + str(each[1]))
    with open('./res/entities.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(tmp))


if __name__ == "__main__":
    post_process(mode='test')
    remove_entity()
