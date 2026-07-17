import math


def average_precision(ranked_doc_ids, relevant_doc_ids):
    if not relevant_doc_ids:
        return 0.0

    hit_count = 0
    sum_precision = 0.0

    for i, doc_id in enumerate(ranked_doc_ids):
        if str(doc_id) in [str(r) for r in relevant_doc_ids]:
            hit_count += 1
            precision_at_i = hit_count / (i + 1)
            sum_precision += precision_at_i

    return sum_precision / len(relevant_doc_ids)


def mean_average_precision(all_ranked, all_relevant):
    if not all_ranked:
        return 0.0

    ap_sum = 0.0
    for ranked, relevant in zip(all_ranked, all_relevant):
        ap_sum += average_precision(ranked, relevant)

    return ap_sum / len(all_ranked)


def reciprocal_rank(ranked_doc_ids, relevant_doc_ids):
    if not relevant_doc_ids:
        return 0.0

    for i, doc_id in enumerate(ranked_doc_ids):
        if str(doc_id) in [str(r) for r in relevant_doc_ids]:
            return 1.0 / (i + 1)
    return 0.0


def mean_reciprocal_rank(all_ranked, all_relevant):
    if not all_ranked:
        return 0.0

    rr_sum = 0.0
    for ranked, relevant in zip(all_ranked, all_relevant):
        rr_sum += reciprocal_rank(ranked, relevant)

    return rr_sum / len(all_ranked)


def ndcg_at_k(ranked_doc_ids, relevant_doc_ids, k=5):
    if not relevant_doc_ids:
        return 0.0

    dcg = 0.0
    for i, doc_id in enumerate(ranked_doc_ids[:k]):
        if str(doc_id) in [str(r) for r in relevant_doc_ids]:
            dcg += 1.0 / math.log2((i + 1) + 1)

    idcg = 0.0
    num_ideal_docs = min(len(relevant_doc_ids), k)
    for i in range(num_ideal_docs):
        idcg += 1.0 / math.log2((i + 1) + 1)

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def mean_ndcg_at_k(all_ranked, all_relevant, k=5):
    if not all_ranked:
        return 0.0

    ndcg_sum = 00
    for ranked, relevant in zip(all_ranked, all_relevant):
        ndcg_sum += ndcg_at_k(ranked, relevant, k)

    return ndcg_sum / len(all_ranked)


def evaluate_all(tfidf_results, semantic_results, ground_truth):
    all_relevant = [q["relevant_doc_ids"] for q in ground_truth]

    all_ranked_tfidf = []
    for res_list in tfidf_results:
        all_ranked_tfidf.append(
            [str(item.get("id_str", item.get("id"))) for item in res_list]
        )

    all_ranked_semantic = []
    for res_list in semantic_results:
        all_ranked_semantic.append(
            [str(item.get("id_str", item.get("id"))) for item in res_list]
        )

    metrics = {
        "tfidf": {
            "map": round(mean_average_precision(all_ranked_tfidf, all_relevant), 4),
            "mrr": round(mean_reciprocal_rank(all_ranked_tfidf, all_relevant), 4),
            "ndcg_5": round(mean_ndcg_at_k(all_ranked_tfidf, all_relevant, k=5), 4),
        },
        "semantic": {
            "map": round(mean_average_precision(all_ranked_semantic, all_relevant), 4),
            "mrr": round(mean_reciprocal_rank(all_ranked_semantic, all_relevant), 4),
            "ndcg_5": round(mean_ndcg_at_k(all_ranked_semantic, all_relevant, k=5), 4),
        },
    }

    return metrics
