import math
import re
import pandas as pd

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory


class TFIDFSearchEngine:
    def __init__(self, df):
        factory = StemmerFactory()
        self.stemmer = factory.create_stemmer()
        self.sw_sastrawi = set(StopWordRemoverFactory().get_stop_words())

        self.doc_lookup = df.set_index(df["id_str"].astype(str)).to_dict("index")
        self.total_docs = len(df)

        inverted_index = self._build_inverted_index(df)
        self.tfidf_index, self.idf_dict, self.doc_magnitudes = self._calculate_tfidf(
            inverted_index
        )

    def _text_preprocessing(self, text):
        cleaned_text = text.lower()
        cleaned_text = re.sub(r"@\w+|#\w+", "", cleaned_text)
        cleaned_text = cleaned_text.encode("ascii", "ignore").decode("ascii")
        cleaned_text = re.sub(r"[0-9]+", "", cleaned_text)
        cleaned_text = re.sub(r"[^\w\s]", " ", cleaned_text)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

        raw_tokens = cleaned_text.split()
        filtered_tokens = [
            t for t in raw_tokens if t not in self.sw_sastrawi and len(t) >= 3
        ]
        tokens = [self.stemmer.stem(t) for t in filtered_tokens]

        return " ".join(tokens), tokens

    def _build_inverted_index(self, df):
        inverted_index = {}
        for _, row in df.iterrows():
            doc_id = str(row["id_str"])
            text = row["komentar"]

            _, tokens = self._text_preprocessing(text)
            if not tokens:
                continue

            for token in tokens:
                if token not in inverted_index:
                    inverted_index[token] = {}
                inverted_index[token][doc_id] = inverted_index[token].get(doc_id, 0) + 1
        return inverted_index

    def _calculate_tfidf(self, inverted_index):
        tfidf_index = {}
        idf_dict = {}
        doc_length_sq = {}

        for term, doc_dict in inverted_index.items():
            df_t = len(doc_dict)

            idf = math.log10((self.total_docs + 1) / (df_t + 1)) + 1
            idf_dict[term] = idf

            tfidf_index[term] = {}
            for doc_id, raw_tf in doc_dict.items():
                log_tf = (1 + math.log10(raw_tf)) if raw_tf > 0 else 0
                weight = log_tf * idf
                tfidf_index[term][doc_id] = weight

                doc_length_sq[doc_id] = doc_length_sq.get(doc_id, 0) + weight**2

        doc_magnitudes = {doc_id: math.sqrt(sq) for doc_id, sq in doc_length_sq.items()}
        return tfidf_index, idf_dict, doc_magnitudes

    def search(self, query: str, top_k=None):
        _, query_tokens = self._text_preprocessing(query)
        if not query_tokens:
            return []

        query_raw_tf = {}
        for token in query_tokens:
            query_raw_tf[token] = query_raw_tf.get(token, 0) + 1

        query_tfidf = {}
        query_length_sq = 0.0

        for term, raw_tf in query_raw_tf.items():
            if term not in self.idf_dict:
                continue
            log_tf = (1 + math.log10(raw_tf)) if raw_tf > 0 else 0
            weight = log_tf * self.idf_dict[term]
            query_tfidf[term] = weight
            query_length_sq += weight**2

        if query_length_sq == 0:
            return []

        query_magnitude = math.sqrt(query_length_sq)

        dot_products = {}
        for term, q_weight in query_tfidf.items():
            if term in self.tfidf_index:
                for doc_id, d_weight in self.tfidf_index[term].items():
                    dot_products[doc_id] = dot_products.get(doc_id, 0) + (
                        q_weight * d_weight
                    )

        if not dot_products:
            return []

        scores = []
        for doc_id, dot_prod in dot_products.items():
            denom = query_magnitude * self.doc_magnitudes.get(doc_id, 1.0)
            if denom == 0:
                continue
            similarity = dot_prod / denom

            row_data = self.doc_lookup[doc_id]
            scores.append(
                {
                    "id_str": doc_id,
                    "komentar": row_data["komentar"],
                    "score": round(similarity, 4),
                }
            )

        scores = sorted(scores, key=lambda x: x["score"], reverse=True)

        if top_k:
            scores = scores[:top_k]

        return scores
