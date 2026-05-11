from __future__ import annotations


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SHL Assessment Recommender</title>
  <style>
    :root {
      --bg: #f4efe6;
      --panel: rgba(255, 252, 246, 0.9);
      --panel-strong: #fffdf8;
      --text: #1d2430;
      --muted: #687282;
      --line: rgba(29, 36, 48, 0.12);
      --brand: #0d6b5d;
      --brand-2: #d68c45;
      --user: #113b5d;
      --assistant: #e8f4ee;
      --shadow: 0 20px 45px rgba(37, 43, 58, 0.12);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(214, 140, 69, 0.24), transparent 26%),
        radial-gradient(circle at right 20%, rgba(13, 107, 93, 0.18), transparent 24%),
        linear-gradient(135deg, #f7f2e8 0%, #efe7da 46%, #f5efe7 100%);
      min-height: 100vh;
    }

    .shell {
      width: min(1180px, calc(100% - 32px));
      margin: 24px auto;
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
      gap: 20px;
    }

    .panel {
      background: var(--panel);
      border: 1px solid rgba(255, 255, 255, 0.55);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(10px);
    }

    .sidebar {
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 11px;
      color: var(--brand);
      margin-bottom: 10px;
      font-family: Arial, sans-serif;
      font-weight: 700;
    }

    h1 {
      margin: 0;
      font-size: 34px;
      line-height: 1;
      font-weight: 700;
    }

    .subcopy,
    .stat p,
    .scenario p,
    .empty,
    .hint,
    .meta,
    .pill {
      font-family: Arial, sans-serif;
    }

    .subcopy {
      margin: 0;
      color: var(--muted);
      line-height: 1.6;
      font-size: 14px;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }

    .stat {
      padding: 14px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.62);
      border: 1px solid var(--line);
    }

    .stat strong {
      display: block;
      font-size: 20px;
      margin-bottom: 6px;
    }

    .stat p {
      margin: 0;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
    }

    .scenario-list {
      display: grid;
      gap: 10px;
    }

    .scenario {
      width: 100%;
      text-align: left;
      border: 1px solid var(--line);
      background: var(--panel-strong);
      border-radius: 18px;
      padding: 14px 15px;
      cursor: pointer;
      transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
    }

    .scenario:hover {
      transform: translateY(-1px);
      box-shadow: 0 12px 24px rgba(26, 33, 45, 0.08);
      border-color: rgba(13, 107, 93, 0.35);
    }

    .scenario strong {
      display: block;
      font-size: 15px;
      margin-bottom: 6px;
    }

    .scenario p {
      margin: 0;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
    }

    .workspace {
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      min-height: calc(100vh - 48px);
      overflow: hidden;
    }

    .topbar {
      padding: 22px 24px 14px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }

    .topbar h2 {
      margin: 0;
      font-size: 26px;
    }

    .meta {
      color: var(--muted);
      font-size: 13px;
    }

    .chat-scroll {
      padding: 20px 24px 8px;
      overflow-y: auto;
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 18px;
      align-items: start;
    }

    .conversation {
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-height: 100%;
    }

    .bubble {
      max-width: 86%;
      padding: 16px 18px;
      border-radius: 22px;
      box-shadow: 0 8px 24px rgba(31, 40, 54, 0.08);
      animation: rise 220ms ease;
    }

    .bubble.user {
      align-self: flex-end;
      background: linear-gradient(135deg, var(--user), #1f587f);
      color: white;
      border-bottom-right-radius: 8px;
    }

    .bubble.assistant {
      align-self: flex-start;
      background: var(--assistant);
      border: 1px solid rgba(13, 107, 93, 0.1);
      border-bottom-left-radius: 8px;
    }

    .bubble .label {
      display: block;
      margin-bottom: 6px;
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      opacity: 0.7;
      font-family: Arial, sans-serif;
      font-weight: 700;
    }

    .bubble p {
      margin: 0;
      line-height: 1.6;
      font-size: 15px;
      word-break: break-word;
    }

    .side-results {
      position: sticky;
      top: 0;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .results-card {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.68);
      border-radius: 22px;
      padding: 18px;
    }

    .results-card h3 {
      margin: 0 0 10px;
      font-size: 18px;
    }

    .empty {
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
      font-size: 13px;
    }

    .recommendations {
      display: grid;
      gap: 10px;
    }

    .recommendation {
      display: block;
      text-decoration: none;
      color: inherit;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: #fffdfa;
      padding: 14px;
      transition: transform 160ms ease, border-color 160ms ease;
    }

    .recommendation:hover {
      transform: translateY(-1px);
      border-color: rgba(214, 140, 69, 0.5);
    }

    .recommendation strong {
      display: block;
      margin-bottom: 6px;
      font-size: 14px;
    }

    .pill {
      display: inline-flex;
      padding: 4px 9px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.04em;
      background: rgba(13, 107, 93, 0.1);
      color: var(--brand);
      margin-bottom: 8px;
    }

    .hint {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
      margin: 0;
    }

    .composer {
      padding: 16px 24px 24px;
      border-top: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255,255,255,0.2), rgba(255,255,255,0.56));
    }

    .controls {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: end;
    }

    textarea {
      width: 100%;
      min-height: 96px;
      resize: vertical;
      border-radius: 18px;
      border: 1px solid var(--line);
      padding: 15px 16px;
      font: 14px/1.55 Arial, sans-serif;
      color: var(--text);
      background: rgba(255, 255, 255, 0.92);
      outline: none;
    }

    textarea:focus {
      border-color: rgba(13, 107, 93, 0.45);
      box-shadow: 0 0 0 4px rgba(13, 107, 93, 0.08);
    }

    .button-row {
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: flex-end;
      flex-wrap: wrap;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      cursor: pointer;
      font: 700 13px Arial, sans-serif;
      transition: transform 160ms ease, opacity 160ms ease, box-shadow 160ms ease;
    }

    button:hover {
      transform: translateY(-1px);
    }

    .primary {
      color: white;
      background: linear-gradient(135deg, var(--brand), #0f7e6d);
      box-shadow: 0 10px 24px rgba(13, 107, 93, 0.22);
    }

    .ghost {
      background: rgba(255, 255, 255, 0.75);
      color: var(--text);
      border: 1px solid var(--line);
    }

    .status {
      min-height: 18px;
      margin-top: 10px;
      color: var(--muted);
      font: 12px Arial, sans-serif;
    }

    @keyframes rise {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    @media (max-width: 980px) {
      .shell {
        grid-template-columns: 1fr;
      }

      .workspace {
        min-height: auto;
      }

      .chat-scroll {
        grid-template-columns: 1fr;
      }

      .side-results {
        position: static;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <aside class="panel sidebar">
      <div>
        <div class="eyebrow">SHL Labs Assignment</div>
        <h1>Conversational Assessment Recommender</h1>
      </div>
      <p class="subcopy">
        This interactive layer sits on top of the assignment API. It helps an interviewer test vague queries,
        refinement, and grounded comparison in a few clicks.
      </p>

      <section class="stats">
        <div class="stat">
          <strong>/health</strong>
          <p>Readiness check stays available for deployment evaluators.</p>
        </div>
        <div class="stat">
          <strong>/chat</strong>
          <p>Stateless endpoint powers the full conversation history flow.</p>
        </div>
      </section>

      <section>
        <div class="eyebrow">Try Scenarios</div>
        <div class="scenario-list">
          <button class="scenario" data-prompt="I need an assessment for a role I am hiring for.">
            <strong>Vague Query</strong>
            <p>Checks whether the assistant asks a clarifying question before recommending.</p>
          </button>
          <button class="scenario" data-prompt="Hiring a Java developer who works with stakeholders.">
            <strong>Technical + Stakeholder Fit</strong>
            <p>Tests mixed technical and personality coverage for a software hiring case.</p>
          </button>
          <button class="scenario" data-prompt="Actually, add personality tests too.">
            <strong>Mid-Conversation Refinement</strong>
            <p>Use this after a first shortlist to verify that edits update recommendations.</p>
          </button>
          <button class="scenario" data-prompt="What is the difference between OPQ and G+?">
            <strong>Grounded Comparison</strong>
            <p>Checks comparison behavior using assessment aliases instead of full names.</p>
          </button>
        </div>
      </section>
    </aside>

    <section class="panel workspace">
      <header class="topbar">
        <div>
          <div class="eyebrow">Live Demo</div>
          <h2>Interviewer Dashboard</h2>
        </div>
        <div class="meta" id="meta">Conversation turns: 0</div>
      </header>

      <div class="chat-scroll">
        <section class="conversation" id="conversation">
          <div class="bubble assistant">
            <span class="label">Assistant</span>
            <p>Describe the role you are hiring for, paste a short job description, or ask me to compare two SHL assessments.</p>
          </div>
        </section>

        <aside class="side-results">
          <div class="results-card">
            <h3>Latest Shortlist</h3>
            <div id="recommendations">
              <p class="empty">Recommendations will appear here after the agent has enough context.</p>
            </div>
          </div>

          <div class="results-card">
            <h3>Why this demo helps</h3>
            <p class="hint">
              It makes the assignment easier to evaluate because the interviewer can see the stateless conversation,
              the structured shortlist, and the agent's refinement behavior in one place.
            </p>
          </div>
        </aside>
      </div>

      <footer class="composer">
        <div class="controls">
          <textarea id="messageInput" placeholder="Example: Hiring a mid-level Java developer who works with stakeholders and may need personality coverage."></textarea>
          <div class="button-row">
            <button class="ghost" id="resetButton" type="button">Reset</button>
            <button class="primary" id="sendButton" type="button">Send</button>
          </div>
        </div>
        <div class="status" id="status"></div>
      </footer>
    </section>
  </main>

  <script>
    const messages = [];
    const conversationEl = document.getElementById("conversation");
    const recommendationsEl = document.getElementById("recommendations");
    const statusEl = document.getElementById("status");
    const metaEl = document.getElementById("meta");
    const inputEl = document.getElementById("messageInput");
    const sendButton = document.getElementById("sendButton");
    const resetButton = document.getElementById("resetButton");

    function renderBubble(role, content) {
      const article = document.createElement("article");
      article.className = `bubble ${role}`;
      article.innerHTML = `<span class="label">${role === "user" ? "User" : "Assistant"}</span><p></p>`;
      article.querySelector("p").textContent = content;
      conversationEl.appendChild(article);
      conversationEl.scrollTop = conversationEl.scrollHeight;
    }

    function renderRecommendations(items, finished) {
      if (!items.length) {
        recommendationsEl.innerHTML = '<p class="empty">Recommendations will appear here after the agent has enough context.</p>';
        return;
      }

      recommendationsEl.innerHTML = "";
      const wrapper = document.createElement("div");
      wrapper.className = "recommendations";

      items.forEach((item) => {
        const link = document.createElement("a");
        link.className = "recommendation";
        link.href = item.url;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.innerHTML = `
          <span class="pill">Type ${item.test_type}</span>
          <strong>${item.name}</strong>
          <div class="hint">${item.url}</div>
        `;
        wrapper.appendChild(link);
      });

      if (finished) {
        const note = document.createElement("p");
        note.className = "hint";
        note.textContent = "The agent marked this conversation as complete after producing the shortlist.";
        recommendationsEl.appendChild(note);
      }

      recommendationsEl.appendChild(wrapper);
    }

    function syncMeta() {
      const userTurns = messages.filter((item) => item.role === "user").length;
      metaEl.textContent = `Conversation turns: ${messages.length}`;
      if (userTurns >= 8) {
        statusEl.textContent = "Warning: the assignment evaluator caps conversations at 8 total turns.";
      }
    }

    function setBusy(isBusy, label = "") {
      sendButton.disabled = isBusy;
      inputEl.disabled = isBusy;
      statusEl.textContent = label;
    }

    async function sendMessage(text) {
      const value = text.trim();
      if (!value) {
        statusEl.textContent = "Enter a hiring prompt before sending.";
        return;
      }

      messages.push({ role: "user", content: value });
      renderBubble("user", value);
      inputEl.value = "";
      syncMeta();
      setBusy(true, "Thinking through the SHL catalog...");

      try {
        const response = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ messages })
        });

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const data = await response.json();
        messages.push({ role: "assistant", content: data.reply });
        renderBubble("assistant", data.reply);
        renderRecommendations(data.recommendations || [], data.end_of_conversation);
        syncMeta();

        statusEl.textContent = data.end_of_conversation
          ? "Conversation complete. You can still refine the shortlist with another follow-up."
          : "Ready for the next turn.";
      } catch (error) {
        statusEl.textContent = error.message || "Something went wrong while contacting /chat.";
      } finally {
        setBusy(false, statusEl.textContent);
        inputEl.focus();
      }
    }

    sendButton.addEventListener("click", () => sendMessage(inputEl.value));

    inputEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage(inputEl.value);
      }
    });

    resetButton.addEventListener("click", () => {
      messages.length = 0;
      conversationEl.innerHTML = `
        <div class="bubble assistant">
          <span class="label">Assistant</span>
          <p>Describe the role you are hiring for, paste a short job description, or ask me to compare two SHL assessments.</p>
        </div>
      `;
      recommendationsEl.innerHTML = '<p class="empty">Recommendations will appear here after the agent has enough context.</p>';
      statusEl.textContent = "Conversation reset.";
      syncMeta();
      inputEl.focus();
    });

    document.querySelectorAll(".scenario").forEach((button) => {
      button.addEventListener("click", () => {
        inputEl.value = button.dataset.prompt || "";
        inputEl.focus();
      });
    });
  </script>
</body>
</html>
"""
