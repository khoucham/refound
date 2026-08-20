const API = "http://127.0.0.1:5000/api";

/* ---------- index.html: report form ---------- */
const reportType = document.getElementById("reportType");
if (reportType) {
  const foundOnly = document.getElementById("foundOnly");
  reportType.addEventListener("change", () =>
    foundOnly.classList.toggle("hidden", reportType.value !== "found"));

  document.getElementById("suggestBtn").addEventListener("click", async () => {
    const desc = document.getElementById("description").value;
    const r = await fetch(`${API}/suggest-category`, {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({description: desc})
    });
    const data = await r.json();
    const out = document.getElementById("suggestion");
    if (data.category) {
      document.getElementById("category").value = data.category;
      out.textContent = ` Suggested: ${data.category} (${Math.round(data.confidence*100)}% sure)`;
    } else {
      out.textContent = " " + (data.error || "Could not classify");
    }
  });

  document.getElementById("submitBtn").addEventListener("click", async () => {
    const body = {
      report_type: reportType.value,
      category: document.getElementById("category").value,
      description: document.getElementById("description").value,
      location: document.getElementById("location").value,
      date_reported: document.getElementById("date").value,
      contact_email: document.getElementById("email").value,
      secret_question: document.getElementById("secretQ").value,
      secret_answer: document.getElementById("secretA").value,
    };
    const r = await fetch(`${API}/reports`, {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    const data = await r.json();
    const out = document.getElementById("result");
    if (r.ok) {
      out.innerHTML = `<p class="success">Report #${data.id} submitted.
        ${data.matches.length} possible match(es) found —
        <a href="browse.html">view them on the Browse page</a>.</p>`;
    } else {
      out.innerHTML = `<p class="fail">${data.error}</p>`;
    }
  });
}

/* ---------- browse.html: list, matches, verification ---------- */
const reportList = document.getElementById("reportList");
if (reportList) {
  loadReports();
  document.getElementById("filterBtn").addEventListener("click", loadReports);

  async function loadReports() {
    const type = document.getElementById("filterType").value;
    const search = document.getElementById("filterSearch").value;
    const params = new URLSearchParams();
    if (type) params.set("type", type);
    if (search) params.set("search", search);
    const r = await fetch(`${API}/reports?` + params);
    const rows = await r.json();
    reportList.innerHTML = rows.slice(0, 30).map(rep => `
      <div class="card">
        <span class="badge ${rep.report_type}">${rep.report_type}</span>
        <strong> ${rep.category}</strong> — ${rep.description}
        <br><small>${rep.location || ""} ${rep.date_reported || ""}</small>
        ${rep.photo_url ? `<br><img class="thumb" src="${rep.photo_url}">` : ""}
        ${rep.report_type === "lost" && rep.status === "open"
          ? `<br><button onclick="showMatches(${rep.id})">Find matches</button>` : ""}
      </div>`).join("");
  }

  window.showMatches = async (lostId) => {
    const r = await fetch(`${API}/reports/${lostId}/matches`);
    const matches = await r.json();
    const panel = document.getElementById("matchPanel");
    panel.classList.remove("hidden");
    panel.scrollIntoView({behavior: "smooth"});
    if (!matches.length) {
      panel.innerHTML = "<h3>No matches yet</h3><p>Check back later.</p>";
      return;
    }
    panel.innerHTML = "<h3>Top suggested matches</h3>" + matches.map(m => `
      <div class="card">
        <span class="sim">${Math.round(m.similarity*100)}% similar</span> —
        ${m.description}<br><small>${m.location || ""}</small>
        ${m.photo_url ? `<br><img class="thumb" src="${m.photo_url}">` : ""}
        <br><button onclick="startVerify(${lostId}, ${m.id})">This is mine</button>
        <div id="verify-${m.id}"></div>
      </div>`).join("");
  };

  window.startVerify = async (lostId, foundId) => {
    const r = await fetch(`${API}/reports/${foundId}/question`);
    const data = await r.json();
    const box = document.getElementById(`verify-${foundId}`);
    if (!r.ok) { box.innerHTML = `<p class="fail">${data.error}</p>`; return; }
    box.innerHTML = `
      <label>${data.secret_question}</label>
      <input id="ans-${foundId}" placeholder="Your answer">
      <button onclick="submitVerify(${lostId}, ${foundId})">Verify</button>
      <div id="vres-${foundId}"></div>`;
  };

  window.submitVerify = async (lostId, foundId) => {
    const answer = document.getElementById(`ans-${foundId}`).value;
    const r = await fetch(`${API}/verify`, {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({lost_report_id: lostId, found_report_id: foundId, answer})
    });
    const data = await r.json();
    const out = document.getElementById(`vres-${foundId}`);
    if (data.passed) {
      out.innerHTML = `<p class="success">Verified! Contact the finder:
                       <strong>${data.contact_email}</strong></p>`;
    } else if (data.error) {
      out.innerHTML = `<p class="fail">${data.error}</p>`;
    } else {
      out.innerHTML = `<p class="fail">Not verified (score ${data.score}).
                       Attempts left: ${data.attempts_left}</p>`;
    }
  };
}