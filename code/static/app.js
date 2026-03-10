const chat = document.getElementById("chat");
const form = document.getElementById("chatForm");
const input = document.getElementById("queryInput");
const sendBtn = document.getElementById("sendBtn");
const ragToggle = document.getElementById("ragToggle");

const escapeHtml = (text = "") =>
  String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const formatInlineBold = (text = "") =>
  escapeHtml(text).replace(/\*\*([\s\S]+?)\*\*/g, "<strong>$1</strong>");

const formatMultiline = (text = "") =>
  formatInlineBold(text).replace(/\r?\n/g, "<br>");

const renderCitations = (citations = []) => {
  if (!Array.isArray(citations) || citations.length === 0) {
    return "";
  }

  const items = citations
    .map((cite) => {
      const act = cite.act || "unknown";
      const section = cite.section || "n/a";
      const subsection = cite.subsection || "n/a";
      const source = cite.source || "";
      const downloadButton = source
        ? `<button class="citation-download" data-source="${source}" type="button">Download PDF</button>`
        : "";
      return `
        <div class="citation-card">
          <div class="citation-pill">
            <span class="citation-icon" aria-hidden="true"></span>
            <span>act: ${act}</span>
          </div>
          <div class="citation-meta">
            <span>section: ${section}</span>
            <span>subsection: ${subsection}</span>
          </div>
          ${downloadButton}
        </div>
      `;
    })
    .join("");

  return `<div class="citations">${items}</div>`;
};

const addMessage = (text, role, options = {}) => {
  const message = document.createElement("div");
  message.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  if (options.typing) {
    bubble.innerHTML = `
      <div class="typing">
        <span></span><span></span><span></span>
      </div>
    `;
  } else {
    bubble.innerHTML = formatMultiline(text);
  }

  message.appendChild(bubble);
  chat.appendChild(message);
  chat.scrollTop = chat.scrollHeight;
  return bubble;
};

const autoGrow = () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
};

input.addEventListener("input", autoGrow);

chat.addEventListener("click", async (event) => {
  const target = event.target.closest(".citation-download");
  if (!target) {
    return;
  }

  const source = target.dataset.source;
  if (!source) {
    return;
  }

  target.disabled = true;
  try {
    const response = await fetch("/api/citation-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source }),
    });
    if (!response.ok) {
      target.disabled = false;
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${source}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    target.disabled = false;
  } finally {
    target.disabled = false;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query) {
    return;
  }

  addMessage(query, "user");
  input.value = "";
  autoGrow();

  sendBtn.disabled = true;
  const typingBubble = addMessage("", "assistant", { typing: true });

  try {
    const useMockPayload = false; // Set to true to use the mock response instead of making an API call
    let data;

    if (useMockPayload) {
      data = {
        answer:
          "**අධිකාරියේ සභාපතිවරයා** සහ පූර්ණ කාලීන සාමාජිකයන්‌ ඔවුන්ගේ පත්වීම්වල දින සිට අවුරුදු තුනක කාලයක්‌ සඳහා ධුරය දැරිය යුතු අතර, සභාවේ සාමාජිකයන්‌ ද අවුරුදු තුනක කාලයක්‌ ධුර දැරිය යුතුය.",
        citations: [
          {
            act: "2003 අංක 9  පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනත",
            section: "4",
            source: "Consumer_Affairs_Authority_ActNo9_of_2003",
            subsection: "None",
          },
          {
            act: "2003 අංක 9  පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනත",
            section: "39",
            source: "Consumer_Affairs_Authority_ActNo9_of_2003",
            subsection: "3",
          },
        ],
      };
    } else {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          ragenable: Boolean(ragToggle && ragToggle.checked),
        }),
      });
      data = await response.json();
      if (!response.ok) {
        typingBubble.textContent = data.error || "Something went wrong.";
        return;
      }
    }
    typingBubble.innerHTML = "";

    let answer = data.answer || (data.parsed && data.parsed.answer) || "";
    let citations =
      data.citations || (data.parsed && data.parsed.citations) || [];
    const rawResponse = data.response || "";

    if (!answer && rawResponse) {
      const fenceMatch = rawResponse.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
      const candidate = fenceMatch ? fenceMatch[1].trim() : rawResponse;
      try {
        const parsed = JSON.parse(candidate);
        answer = parsed.answer || "";
        citations = parsed.citations || [];
      } catch (err) {
        answer = candidate;
        citations = [];
      }
    }

    if (answer) {
      const formattedAnswer = formatInlineBold(answer);
      const answerHtml = `
        <div class="answer-text">${formattedAnswer}</div>
        ${renderCitations(citations)}
      `;
      typingBubble.innerHTML = answerHtml;
    } else {
      typingBubble.textContent = "No response returned.";
    }
  } catch (error) {
    typingBubble.innerHTML = "";
    typingBubble.textContent = "Network error. Please try again.";
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
});
