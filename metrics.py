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
    counter = {}
    for word in splitted_text:
        counter[word] = sum([1 for w in splitted_text if w == word or
                             jaro(w, word) >= 0.9])
    tf = {}
    for word in counter:
        tf[word] = counter[word] / float(len(splitted_text))
    return tf

def get_idf(word, corpus):
    documents_with_word = sum([1.0 for doc in corpus
                               if word_in_doc(word, doc)])
    if documents_with_word > 0:
        return 1.0 + math.log(float(len(corpus)) / documents_with_word)
    else:
        return 1.0

def word_in_doc(word, doc):
    words = doc.split()
    return word in words or sum([1 for w in words if jaro(w, word) >= 0.9]) > 0

def get_tfidf(word, doc, corpus):
    tf = get_tf(doc)[word]
    idf = get_idf(word, corpus)
    return math.log(tf + 1) * math.log(idf)

def get_dot_product(vector1, vector2):
    if len(vector1) != len(vector2):
        return 0
    return sum(i[0] * i[1] for i in zip(vector1, vector2))

def get_vector_len(vector):
    return math.sqrt(sum(i ** 2 for i in vector))

def cosine_similarity(query, document):
    # if not (any(query) and any(document)):
    #     return 0
    return (get_dot_product(query, document) /
            (get_vector_len(query) * get_vector_len(document)))

def get_tfidf_cosine_similarity(query, texts):
    text_tfidfs = {}
    for text in texts:
        sim_text = [w if w == v or jaro(w, v) >= 0.9 else v
                    for w in query.split() for v in text.split()]
        print(sim_text)
        similar_words = [w for w in query.split() for v in text.split()
                         if w == v or jaro(w, v) >= 0.9]
        text_tfidfs[text] = [get_tfidf(word, text, texts)
                             for word in similar_words]
    query_tfidf = [get_tfidf(word, query, texts)
                   for word in query.split()]

    return [cosine_similarity(query_tfidf, text_tfidfs[text])
            for text in text_tfidfs]

