def get_tfidf(word, doc, corpus):
    tf = get_tf(doc)[word]
    idf = get_idf(word, corpus)
    return tf * idf

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
    for text in texts:
        text_tfidfs[text] = [get_tfidf(word, text, texts)
                             for word in query.split()]
    query_tfidf = [get_tfidf(word, query, texts)
                   for word in query.split()]
    return [cosine_similarity(query_tfidf, text_tfidfs[text])
            for text in text_tfidfs]
