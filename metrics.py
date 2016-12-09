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

def get_tf(text):
    splitted_text = text.split()
    tf = Counter(splitted_text)
    for word in tf:
        tf[word] = tf[word] / float(len(splitted_text))
    return tf

def get_idf(word, corpus):
    documents_with_word = sum([1.0 for doc in corpus
                               if word in doc])
    if documents_with_word > 0:
        return math.log(float(len(corpus)) / documents_with_word)
    else:
        return 1.0

def word_in_doc(word, doc):
    words = doc.split()
    return word in words or sum([1 for w in words if jaro(w, word) >= 0.9]) > 0

def get_tfidf(word, doc, corpus):
    tf = get_tf(doc)[word]
    idf = get_idf(word, corpus)
    return math.log(tf) * idf

def get_dot_product(vector1, vector2):
    if len(vector1) != len(vector2):
        return 0
    return sum(i[0] * i[1] for i in zip(vector1, vector2))

def get_vector_len(vector):
    return math.sqrt(sum(i ** 2 for i in vector))

def cosine_similarity(query, document):
    if not (any(query) and any(document)):
        return 0
    return (get_dot_product(query, document) /
            (get_vector_len(query) * get_vector_len(document)))

def get_tfidf_cosine_similarity(query, texts):
    text_tfidfs = {}
    for i in range(len(texts)):
        sim_text = texts[i].split()
        for j in range(len(sim_text)):
            for w in query.split():
                if jaro(sim_text[j], w) >= 0.9:
                    sim_text[j] = w
        similar_words = [w for w in query.split() for v in sim_text if w == v]
        text = ' '.join(sim_text)
        texts[i] = text
        text_tfidfs[text] = [get_tfidf(word, text, texts)
                             for word in similar_words]
    query_tfidf = [get_tfidf(word, query, texts)
                   for word in query.split()]

    return [cosine_similarity(query_tfidf, text_tfidfs[text])
            for text in text_tfidfs]

def get_soft_tfidf(set1, set2, threshold):
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