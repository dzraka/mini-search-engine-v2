from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class SemanticSearchEngine:
    def __init__(self, model_name="firqaaa/indo-sentence-bert-base"):
        self.model = SentenceTransformer(model_name)
        self.doc_embeddings = None
        self.docs = []

    def index_documents(self, df):
        texts = df["komentar"].tolist()
        self.doc_embeddings = self.model.encode(
            texts, show_progress_bar=True, convert_to_numpy=True
        )
        self.docs = df.to_dict("records")

    def search(self, query, top_k=None):
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        similarities = cosine_similarity(query_embedding, self.doc_embeddings)[0]

        results = []
        for idx, score in enumerate(similarities):
            results.append(
                {
                    "id_str": str(self.docs[idx]["id_str"]),
                    "komentar": self.docs[idx]["komentar"],
                    "score": round(float(score), 4),
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        if top_k:
            results = results[:top_k]
        return results
