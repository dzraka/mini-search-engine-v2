document.addEventListener("DOMContentLoaded", function () {
  const tfidfBtn = document.getElementById("tfidf-btn");
  const semanticBtn = document.getElementById("semantic-btn");
  const evaluateBtn = document.getElementById("evaluate-btn");
  const searchInput = document.getElementById("search-input");
  const searchBtn = document.getElementById("search-btn");
  const resultInfo = document.getElementById("result-info");
  const resultsContainer = document.getElementById("results");
  const evaluateContainer = document.getElementById("evaluate-results");
  const paginationContainer = document.getElementById("pagination");

  let currentMethod = "tfidf";

  let currentPage = 1;
  let isSearching = false;
  let currentQuery = "";

  loadAllDocuments(1);

  function loadAllDocuments(page) {
    isSearching = false;
    currentPage = page;

    fetch(`/get-all-docs?page=${page}`)
      .then((response) => response.json())
      .then((data) => {
        displayResults(data, false);
      })
      .catch((error) => console.error("Error:", error));
  }

  tfidfBtn.addEventListener("click", () => setMethod("tfidf"));
  semanticBtn.addEventListener("click", () => setMethod("semantic"));
  evaluateBtn.addEventListener("click", runEvaluation);

  const activeClasses = "bg-blue-600/90 text-white shadow-md shadow-blue-900/50".split(" ");
  const inactiveClasses = "text-slate-400 hover:bg-slate-700/50 hover:text-slate-200 hover:cursor-pointer".split(" ");

  function updateButtonState(btn, isActive) {
    if (isActive) {
      btn.classList.remove(...inactiveClasses);
      // Also remove the malformed 'hover:' if it exists
      btn.classList.remove("hover:", "cursor-pointer");
      btn.classList.add(...activeClasses);
    } else {
      btn.classList.remove(...activeClasses);
      btn.classList.add(...inactiveClasses);
    }
  }

  function setMethod(method) {
    currentMethod = method;
    updateButtonState(tfidfBtn, method === "tfidf");
    updateButtonState(semanticBtn, method === "semantic");
    updateButtonState(evaluateBtn, method === "evaluate");

    if (currentQuery) {
      performSearch();
    } else {
      loadAllDocuments(1);
    }
  }

  function performSearch() {
    const query = searchInput.value.trim();
    if (!query) {
      loadAllDocuments(1);
      return;
    }

    isSearching = true;
    currentQuery = query;
    currentPage = 1;

    evaluateContainer.style.display = "none";

    if (currentMethod === "semantic") {
      performSemanticSearch(query, 1);
    } else {
      performTfidfSearch(query, 1);
    }
  }

  function performTfidfSearch(query, page) {
    fetch(`/search/tfidf?q=${encodeURIComponent(query)}&page=${page}`)
      .then((response) => response.json())
      .then((data) => {
        displayResults(data, true);
      })
      .catch((error) => console.error("Error:", error));
  }

  function performSemanticSearch(query, page) {
    fetch(`/search/semantic?q=${encodeURIComponent(query)}&page=${page}`)
      .then((response) => response.json())
      .then((data) => {
        displayResults(data, true);
      })
      .catch((error) => console.error("Error:", error));
  }

  function runEvaluation() {
    currentMethod = "evaluate";
    updateButtonState(tfidfBtn, false);
    updateButtonState(semanticBtn, false);
    updateButtonState(evaluateBtn, true);

    resultInfo.innerHTML = "<p>Menjalankan Evaluasi... Harap tunggu (ini mungkin memakan waktu)...</p>";
    resultsContainer.style.display = "none";
    paginationContainer.innerHTML = "";
    evaluateContainer.style.display = "block";
    evaluateContainer.innerHTML = "<p>Loading...</p>";

    fetch("/evaluate")
      .then((res) => res.json())
      .then((data) => {
        const metrics = data.metrics_comparison;
        resultInfo.innerHTML = "<p>Hasil Evaluasi Sistem</p>";
        evaluateContainer.innerHTML = `
          <h3>Metrik Evaluasi (Berdasarkan Ground Truth)</h3>
          <table class="w-full border-collapse mt-4 text-sm text-left rounded-xl overflow-hidden shadow-sm border border-slate-700/60">
            <thead>
              <tr>
                <th class="bg-slate-800 px-5 py-4 font-semibold text-slate-300 border-b border-slate-700/60">Metode</th>
                <th class="bg-slate-800 px-5 py-4 font-semibold text-slate-300 border-b border-slate-700/60">MAP</th>
                <th class="bg-slate-800 px-5 py-4 font-semibold text-slate-300 border-b border-slate-700/60">MRR</th>
                <th class="bg-slate-800 px-5 py-4 font-semibold text-slate-300 border-b border-slate-700/60">NDCG@5</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="px-5 py-4 border-b border-slate-700/50 text-slate-300 bg-slate-800/60 backdrop-blur-sm"><strong>TF-IDF</strong></td>
                <td class="px-5 py-4 border-b border-slate-700/50 text-slate-300 bg-slate-800/60 backdrop-blur-sm">${metrics.tfidf.map.toFixed(4)}</td>
                <td class="px-5 py-4 border-b border-slate-700/50 text-slate-300 bg-slate-800/60 backdrop-blur-sm">${metrics.tfidf.mrr.toFixed(4)}</td>
                <td class="px-5 py-4 border-b border-slate-700/50 text-slate-300 bg-slate-800/60 backdrop-blur-sm">${metrics.tfidf.ndcg_5.toFixed(4)}</td>
              </tr>
              <tr>
                <td class="px-5 py-4 border-b border-slate-700/50 text-slate-300 bg-slate-800/60 backdrop-blur-sm"><strong>IndoBERT (Semantic)</strong></td>
                <td class="px-5 py-4 border-b border-slate-700/50 text-slate-300 bg-slate-800/60 backdrop-blur-sm">${metrics.semantic.map.toFixed(4)}</td>
                <td class="px-5 py-4 border-b border-slate-700/50 text-slate-300 bg-slate-800/60 backdrop-blur-sm">${metrics.semantic.mrr.toFixed(4)}</td>
                <td class="px-5 py-4 border-b border-slate-700/50 text-slate-300 bg-slate-800/60 backdrop-blur-sm">${metrics.semantic.ndcg_5.toFixed(4)}</td>
              </tr>
            </tbody>
          </table>
        `;
      })
      .catch((err) => console.error(err));
  }

  function displayResults(data, isSearch) {
    const results = data.results || [];
    const query = data.query || "";
    const total = data.total !== undefined ? data.total : results.length;
    const total_pages = data.total_pages !== undefined ? data.total_pages : 1;
    const page = data.page !== undefined ? data.page : 1;

    resultsContainer.style.display = "block";
    evaluateContainer.style.display = "none";

    if (isSearch) {
      resultInfo.innerHTML = `<p>Hasil untuk "${query}" (${total} hasil)</p>`;
    } else {
      resultInfo.innerHTML = `<p>Semua Komentar (${total} total)</p>`;
    }

    if (results.length === 0) {
      resultsContainer.innerHTML = '<p style="text-align: center; padding: 40px; font-size: 16px;">Tidak ada hasil ditemukan</p>';
      paginationContainer.innerHTML = "";
      return;
    }

    resultsContainer.innerHTML = results
      .map((doc) => {
        let infoContent = "—";
        if (isSearch && doc.score) {
          infoContent = `Similarity: ${doc.score}`;
        }
        return `
        <div class="bg-slate-800/70 backdrop-blur-md p-5 rounded-2xl shadow-sm border border-slate-700/50 flex flex-col sm:flex-row justify-between items-start gap-4 transition-all hover:shadow-md hover:bg-slate-800 hover:-translate-y-0.5 mb-4 w-full">
          <div class="flex-1 text-slate-300 text-[15px] leading-relaxed">
            <p>${doc.komentar}</p>
          </div>
          <div class="bg-blue-900/40 text-blue-300 font-semibold px-3 py-1.5 rounded-lg text-xs whitespace-nowrap border border-blue-800/50">${infoContent}</div>
        </div>
      `;
      })
      .join("");

    // Display pagination
    if (total_pages > 1) {
      displayPagination(page, total_pages, isSearch);
    } else {
      paginationContainer.innerHTML = "";
    }
  }

  function displayPagination(currentPageNum, totalPages, isSearch) {
    let paginationHTML = '<div class="flex justify-center items-center gap-4">';
    const btnClass = "px-5 py-2.5 bg-slate-800 border border-slate-700/60 rounded-xl text-sm font-semibold text-slate-300 hover:bg-slate-700 hover:text-blue-400 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed";
    const spanClass = "text-sm font-medium text-slate-400 bg-slate-800/50 px-4 py-2 rounded-xl border border-slate-700";

    if (currentPageNum > 1) {
      paginationHTML += `<button class="${btnClass}" onclick="previousPage(${isSearch})">← Sebelumnya</button>`;
    } else {
      paginationHTML += `<button class="${btnClass}" disabled>← Sebelumnya</button>`;
    }

    paginationHTML += `<span class="${spanClass}"> Halaman ${currentPageNum} dari ${totalPages} </span>`;

    if (currentPageNum < totalPages) {
      paginationHTML += `<button class="${btnClass}" onclick="nextPage(${isSearch})">Berikutnya →</button>`;
    } else {
      paginationHTML += `<button class="${btnClass}" disabled>Berikutnya →</button>`;
    }

    paginationHTML += "</div>";
    paginationContainer.innerHTML = paginationHTML;
  }

  window.previousPage = function (isSearch) {
    if (currentPage > 1) {
      currentPage--;
      if (isSearch) {
        if (currentMethod === "semantic") {
          performSemanticSearch(currentQuery, currentPage);
        } else {
          performTfidfSearch(currentQuery, currentPage);
        }
      } else {
        loadAllDocuments(currentPage);
      }
    }
  };

  window.nextPage = function (isSearch) {
    currentPage++;
    if (isSearch) {
      if (currentMethod === "semantic") {
        performSemanticSearch(currentQuery, currentPage);
      } else {
        performTfidfSearch(currentQuery, currentPage);
      }
    } else {
      loadAllDocuments(currentPage);
    }
  };

  searchBtn.addEventListener("click", performSearch);
  searchInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") performSearch();
  });
});
