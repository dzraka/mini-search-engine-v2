import pandas as pd
import json
import os

from flask import Flask, request, jsonify, render_template
from tfidf_engine import TFIDFSearchEngine
from semantic_engine import SemanticSearchEngine
from evaluation import evaluate_all

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

komentar_list = []
csv_path = os.path.join(BASE_DIR, "data", "vaksin_campak.csv")
try:
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[1:]:
            line = line.strip()
            if line:
                komentar_list.append(line)
except FileNotFoundError:
    print(f"Error: File {csv_path} tidak ditemukan.")
    exit(1)

df_raw = pd.DataFrame(
    {"id_str": range(1, len(komentar_list) + 1), "komentar": komentar_list}
)
total_docs = len(df_raw)

tfidf_engine = TFIDFSearchEngine(df_raw)

semantic_engine = SemanticSearchEngine()
semantic_engine.index_documents(df_raw)

gt_path = os.path.join(BASE_DIR, "data", "ground_truth.json")
ground_truth = []

if os.path.exists(gt_path):
    try:
        with open(gt_path, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)
        print(f"Berhasil memuat {len(ground_truth)} kueri uji dari ground truth.")
    except json.JSONDecodeError:
        print("Error: Format file ground_truth.json tidak valid.")
else:
    print(f"Peringatan: Berkas ground truth tidak ditemukan di {gt_path}!")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get-all-docs", methods=["GET"])
def get_all_docs():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 10

    all_docs = df_raw[["id_str", "komentar"]].to_dict(orient="records")
    total = len(all_docs)
    start = (page - 1) * per_page
    end = start + per_page

    paginated_docs = all_docs[start:end]
    total_pages = (total + per_page - 1) // per_page

    return jsonify(
        {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "results": paginated_docs,
        }
    )


@app.route("/search/tfidf", methods=["GET"])
def handle_tfidf_search():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"query": query, "results": []})

    results = tfidf_engine.search(query, top_k=5)

    return jsonify({"query": query, "results": results})


@app.route("/search/semantic", methods=["GET"])
def handle_semantic_search():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"query": query, "results": []})

    results = semantic_engine.search(query, top_k=5)

    return jsonify({"query": query, "results": results})


@app.route("/evaluate", methods=["GET"])
def evaluate():
    if not ground_truth:
        return (
            jsonify({"error": "File ground_truth.json kosong atau tidak ditemukan"}),
            404,
        )

    tfidf_all_results = []
    semanctic_all_results = []

    for item in ground_truth:
        query_text = item["query"]

        res_tfidf = tfidf_engine.search(query_text, top_k=5)
        res_semantic = semantic_engine.search(query_text, top_k=5)

        tfidf_all_results.append(res_tfidf)
        semanctic_all_results.append(res_semantic)
    report_metrics = evaluate_all(
        tfidf_all_results, semanctic_all_results, ground_truth
    )
    return jsonify(
        {
            "status": "Evaluasi Berhasil",
            "total_queries_tested": len(ground_truth),
            "metrics_comparison": report_metrics,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
