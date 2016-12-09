from collections import Counter
import math


def jaro(string1, string2):
    str1_len = len(string1)
    str2_len = len(string2)
    match_distance = (max(str1_len, str2_len) // 2) - 1
    str1_matches = [False] * str1_len
    str2_matches = [False] * str2_len
    matches = 0
    transpositions = 0
    for i in range(str1_len):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, str2_len)
        for j in range(start, end):
            if str2_matches[j]:
                continue
            if string1[i] != string2[j]:
                continue
            str1_matches[i] = True
            str2_matches[j] = True
            matches += 1
            break
    if matches == 0:
        return 0
    k = 0
    for i in range(str1_len):
        if not str1_matches[i]:
            continue
        while not str2_matches[k]:
            k += 1
        if string1[i] != string2[k]:
            transpositions += 1
        k += 1
    return ((matches / str1_len) + (matches / str2_len) +
            ((matches - transpositions / 2) / matches)) / 3


def soft_tfidf(set1, set2, threshold):
    set1, set2 = set1.split(), set2.split()
    corpus = [set1, set2]
    corpus_size = len(corpus) * 1.0
    tf_x, tf_y = Counter(set1), Counter(set2)
    element_freq = {}
    total_unique_elements = set()
    for doc in corpus:
        temp_set = set()
        for elem in doc:
            if elem in set1 or elem in set2:
                temp_set.add(elem)
                total_unique_elements.add(elem)
        for elem in temp_set:
            element_freq[elem] = (element_freq[elem] + 1
                                  if elem in element_freq else 1)
    similarity_map = {}
    for x in set1:
        if x not in similarity_map:
            max_score = 0.0
            for y in set2:
                score = jaro(x, y)
                if score > threshold and score > max_score:
                    similarity_map[x] = Similarity(x, y, score)
                    max_score = score
    result, v_x_2, v_y_2 = 0.0, 0.0, 0.0
    for elem in total_unique_elements:
        if elem in similarity_map:
            sim = similarity_map[elem]
            idf_first = (corpus_size if sim.first_string not in element_freq
                         else corpus_size / element_freq[sim.first_string])
            idf_second = (corpus_size if sim.second_string not in element_freq
                          else corpus_size / element_freq[sim.second_string])
            v_x = 0 if sim.first_string not in tf_x else idf_first * tf_x[sim.first_string]
            v_y = 0 if sim.second_string not in tf_y else idf_second * tf_y[sim.second_string]
            result += v_x * v_y * sim.similarity_score
        idf = corpus_size if elem not in element_freq else corpus_size / element_freq[elem]
        v_x = 0 if elem not in tf_x else idf * tf_x[elem]
        v_x_2 += v_x * v_x
        v_y = 0 if elem not in tf_y else idf * tf_y[elem]
        v_y_2 += v_y * v_y
    return result if v_x_2 == 0 else result / (math.sqrt(v_x_2) * math.sqrt(v_y_2))


class Similarity:
    def __init__(self, string1, string2, score):
        self.first_string = string1
        self.second_string = string2
        self.similarity_score = score
