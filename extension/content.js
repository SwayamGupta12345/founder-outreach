(() => {
  if (window.__FOC_INITIALIZED__) return;
  window.__FOC_INITIALIZED__ = true;

  const BACKEND_URL = "http://127.0.0.1:8000";

  function cleanText(text) {
    return (text || "")
      .replace(/\u00a0/g, " ")
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function getElementText(selectors) {
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        const text = cleanText(element.innerText || element.textContent);
        if (text) return text;
      }
    }
    return "";
  }

  function getProfileData() {
    const main = document.querySelector("main");

    const name = getElementText([
      ".text-heading-xlarge",
      "h1"
    ]);

    const headline = getElementText([
      ".text-body-medium.break-words",
      ".text-body-medium"
    ]);

    const location = getElementText([
      ".text-body-small.inline.t-black--light.break-words",
      ".text-body-small"
    ]);

    const mainText = cleanText(
      main?.innerText || document.body?.innerText || ""
    );

    const hiringSignals = [];

    document.querySelectorAll("a").forEach((link) => {
      const text = cleanText(link.innerText || link.textContent);
      const href = link.href || "";

      if (!text) return;

      const hiringPattern =
        /hiring|we.?re hiring|open position|job opening|job opportunity|join our team/i;

      if (hiringPattern.test(text) || /opportunities\/hiring/i.test(href)) {
        hiringSignals.push({
          text,
          href
        });
      }
    });

    const uniqueHiringSignals = [];
    const seenHiring = new Set();

    for (const item of hiringSignals) {
      const key = `${item.text}|${item.href}`;

      if (!seenHiring.has(key)) {
        seenHiring.add(key);
        uniqueHiringSignals.push(item);
      }
    }

    return {
      name,
      headline,
      location,
      mainText: mainText.slice(0, 35000),
      hiringSignals: uniqueHiringSignals.slice(0, 20)
    };
  }

  function getVisiblePageText() {
    const data = getProfileData();

    return cleanText(`
PROFILE NAME:
${data.name || "(not extracted)"}

PROFILE HEADLINE:
${data.headline || "(not extracted)"}

PROFILE LOCATION:
${data.location || "(not extracted)"}

EXPLICIT HIRING SIGNALS:
${data.hiringSignals.length
  ? data.hiringSignals.map((x) => x.text).join("\n")
  : "(none extracted)"}

PROFILE MAIN CONTENT:
${data.mainText}
`);
  }

  function el(tag, className, text = "") {
    const node = document.createElement(tag);

    if (className) node.className = className;
    if (text) node.textContent = text;

    return node;
  }

  function createLauncher() {
    if (document.getElementById("foc-launcher")) return;

    const button = el("button", "", "⚡ Copilot");
    button.id = "foc-launcher";
    button.addEventListener("click", togglePanel);

    document.documentElement.appendChild(button);
  }

  function removePanel() {
    const panel = document.getElementById("foc-panel");
    if (panel) panel.remove();
  }

  function togglePanel() {
    if (document.getElementById("foc-panel")) {
      removePanel();
      return;
    }

    openPanel();
  }

  function openPanel() {
    const panel = el("div");
    panel.id = "foc-panel";

    const header = el("div", "foc-header");
    const heading = el("div");

    heading.innerHTML = `
      <div class="foc-brand">
        Personal LinkedIn Copilot
      </div>
      <div class="foc-subtitle">
        Research the person. Pick your intent. Write naturally.
      </div>
    `;

    const close = el("button", "foc-close", "×");
    close.addEventListener("click", removePanel);

    header.appendChild(heading);
    header.appendChild(close);

    const body = el("div", "foc-body");

    body.appendChild(
      el(
        "div",
        "foc-label",
        "What do you want from this interaction?"
      )
    );

    const INTENTS = [
      {
        value: "job",
        label: "💼 Job opportunity",
        description: "Check hiring, fit and relevant resume."
      },
      {
        value: "founder",
        label: "🚀 Founder",
        description: "Research the founder, company and best way to approach."
      },
      {
        value: "network",
        label: "🤝 Network",
        description: "Find genuine overlap and connect."
      },
      {
        value: "advice",
        label: "💬 Ask for advice",
        description: "Find something specific to ask."
      },
      {
        value: "custom",
        label: "✏️ Custom",
        description: "Tell the copilot exactly what you want."
      }
    ];

    const intentGrid = el("div", "foc-intent-grid");
    let selectedIntent = "network";

    for (const item of INTENTS) {
      const card = el("button", "foc-intent");

      card.dataset.intent = item.value;

      card.innerHTML = `
        <div class="foc-intent-title">
          ${item.label}
        </div>
        <div class="foc-intent-description">
          ${item.description}
        </div>
      `;

      if (item.value === selectedIntent) {
        card.classList.add("selected");
      }

      card.addEventListener("click", () => {
        selectedIntent = item.value;

        document.querySelectorAll(".foc-intent").forEach((button) => {
          button.classList.remove("selected");
        });

        card.classList.add("selected");
        customGoal.style.display =
          item.value === "custom" ? "block" : "none";
      });

      intentGrid.appendChild(card);
    }

    body.appendChild(intentGrid);

    const customGoal = el("textarea", "foc-input");

    customGoal.placeholder =
      "Example: I want to talk to this person about backend engineering and ask how they got into distributed systems.";

    customGoal.style.display = "none";

    body.appendChild(customGoal);

    body.appendChild(
      el("div", "foc-label foc-margin-top", "Tone")
    );

    const tone = el("select", "foc-select");

    const tones = [
      ["natural", "Natural"],
      ["casual", "Casual"],
      ["professional", "Professional"],
      ["technical", "Technical"],
      ["direct", "Direct"]
    ];

    for (const [value, label] of tones) {
      const option = document.createElement("option");

      option.value = value;
      option.textContent = label;

      tone.appendChild(option);
    }

    body.appendChild(tone);

    body.appendChild(
      el(
        "div",
        "foc-label foc-margin-top",
        "Extra context (optional)"
      )
    );

    const extra = el("textarea", "foc-input");

    extra.placeholder =
      "Paste a hiring post, message, role description, something you noticed, or any context you want the AI to know.";

    body.appendChild(extra);

    const analyze = el(
      "button",
      "foc-analyze",
      "Analyze person →"
    );

    body.appendChild(analyze);

    const result = el("div", "foc-result");
    body.appendChild(result);

    analyze.addEventListener("click", async () => {
      analyze.disabled = true;
      analyze.textContent = "Researching...";

      result.innerHTML = `
        <div class="foc-loading-box">
          <div class="foc-spinner"></div>
          <div>
            <strong>Working locally</strong>
            <div>
              Researching the profile + matching your resumes...
            </div>
          </div>
        </div>
      `;

      try {
        const profileData = getProfileData();
        const pageText = getVisiblePageText();

        if (profileData.name && profileData.name.length < 2) {
          throw new Error(
            "Could not identify the LinkedIn profile name. Wait for the page to load."
          );
        }

        if (pageText.length < 100) {
          throw new Error(
            "Not enough LinkedIn text. Wait for the page to load."
          );
        }

        const response = await fetch(`${BACKEND_URL}/screen`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            page_url: location.href,
            page_title: document.title,

            page_text: pageText.slice(0, 30000),

            profile_name: profileData.name,
            profile_headline: profileData.headline,
            profile_location: profileData.location,

            hiring_signals: profileData.hiringSignals,

            intent: selectedIntent,

            custom_goal: customGoal.value.slice(0, 5000),

            extra_context: extra.value.slice(0, 15000),

            tone: tone.value
          })
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail || "Backend request failed"
          );
        }

        renderResult(result, data);
      } catch (error) {
        result.innerHTML = "";

        result.appendChild(
          el("div", "foc-error", error.message)
        );
      } finally {
        analyze.disabled = false;
        analyze.textContent = "Analyze again →";
      }
    });

    panel.appendChild(header);
    panel.appendChild(body);

    document.documentElement.appendChild(panel);
  }

  function addList(parent, title, items) {
    if (!items || items.length === 0) return;

    const section = el("div", "foc-section");

    section.appendChild(
      el("div", "foc-label", title)
    );

    const list = el("ul", "foc-list");

    for (const item of items) {
      list.appendChild(
        el("li", "", item)
      );
    }

    section.appendChild(list);
    parent.appendChild(section);
  }

  function renderResult(parent, result) {
    parent.innerHTML = "";

    const top = el("div", "foc-result-top");

    top.innerHTML = `
      <div>
        <div class="foc-person">
          ${escapeHtml(result.person || "Unknown person")}
        </div>

        <div class="foc-role">
          ${escapeHtml(result.current_role || "")}
          ${result.company ? " · " + escapeHtml(result.company) : ""}
        </div>
      </div>

      <div class="foc-badge">
        ${escapeHtml(result.fit || "unknown")}
      </div>
    `;

    parent.appendChild(top);

    const hiring = el("div", "foc-card");

    hiring.innerHTML = `
      <div class="foc-card-title">
        Hiring / opportunity
      </div>

      <div>
        ${escapeHtml(
          result.detected_opportunity ||
          result.hiring_signal ||
          "No clear hiring signal"
        )}
      </div>
    `;

    parent.appendChild(hiring);

    const resume = el(
      "div",
      "foc-card foc-resume"
    );

    resume.innerHTML = `
      <div class="foc-card-title">
        Resume selected
      </div>

      <strong>
        ${escapeHtml(result.selected_resume || "None")}
      </strong>

      <div class="foc-small">
        ${escapeHtml(result.resume_reason || "")}
      </div>
    `;

    parent.appendChild(resume);

    addList(
      parent,
      "Relevant overlap",
      result.relevant_overlap
    );

    addList(
      parent,
      "Useful facts",
      result.useful_facts
    );

    addList(
      parent,
      "Things you could ask",
      result.things_to_ask
    );

    addList(
      parent,
      "Why",
      result.reasons
    );

    const messageSection = el(
      "div",
      "foc-message-section"
    );

    messageSection.appendChild(
      el("div", "foc-label", "Message")
    );

    const message = el(
      "textarea",
      "foc-message"
    );

    message.value = result.message || "";

    messageSection.appendChild(message);

    const actions = el("div", "foc-actions");

    const copy = el(
      "button",
      "foc-action primary",
      "Copy"
    );

    copy.addEventListener("click", async () => {
      await navigator.clipboard.writeText(
        message.value
      );

      copy.textContent = "Copied ✓";

      setTimeout(() => {
        copy.textContent = "Copy";
      }, 1200);
    });

    const shorter = el(
      "button",
      "foc-action",
      "Shorter"
    );

    shorter.addEventListener("click", () => {
      message.value = message.value
        .replace(/\s+/g, " ")
        .slice(0, 250);
    });

    actions.appendChild(copy);
    actions.appendChild(shorter);

    messageSection.appendChild(actions);
    parent.appendChild(messageSection);

    addList(
      parent,
      "Missing information",
      result.missing_information
    );

    addList(
      parent,
      "Warnings",
      result.warnings
    );

    parent.appendChild(
      el(
        "div",
        "foc-confidence",
        `Confidence: ${result.confidence || "unknown"}`
      )
    );
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  createLauncher();

  setInterval(createLauncher, 1500);
})();