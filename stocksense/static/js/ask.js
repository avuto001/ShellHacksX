/*
 * Ask StockSense chat page.
 *
 * Sends questions to POST /api/chat and shows the answers as chat bubbles.
 * The chat history is saved in sessionStorage so it survives a page refresh
 * (it's cleared when the browser tab is closed).
 *
 * Safety note: user text is always inserted with textContent, never innerHTML,
 * so nobody can inject HTML or scripts through the chat box.
 */
(function () {
  const chat = document.getElementById("chat");
  if (!chat) return;

  const STORAGE_KEY = "stocksense-chat-history";
  const apiUrl = chat.dataset.apiUrl;
  const stockUrl = chat.dataset.stockUrl; // contains "__TICKER__" as a placeholder

  const scroller = document.getElementById("chat-scroller");
  const messageList = document.getElementById("message-list");
  const emptyState = document.getElementById("empty-state");
  const suggestionRow = document.getElementById("suggestion-row");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendButton = document.getElementById("send-button");
  const clearButton = document.getElementById("clear-chat");
  const promptChips = document.querySelectorAll("[data-prompt]");

  // Each item is {role: "user", text} or {role: "ai", reply}
  let history = loadHistory();
  let isLoading = false;


  // ---------- Saving history ----------

  function loadHistory() {
    try {
      const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY));
      return Array.isArray(saved) ? saved : [];
    } catch {
      return []; // storage blocked or corrupted: start fresh
    }
  }

  function saveHistory() {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch {
      // Storage can be blocked (e.g. private mode). The chat still works, it just won't survive a refresh.
    }
  }


  // ---------- Building message bubbles ----------

  // Copy a <template> from ask.html
  function fromTemplate(id) {
    return document.getElementById(id).content.firstElementChild.cloneNode(true);
  }

  function addToChat(element, animate) {
    if (!animate) element.classList.remove("msg-enter");
    messageList.append(element);
    updateLayout();
    window.StockSense.refreshIcons();
    scrollToBottom(animate);
    return element;
  }

  function scrollToBottom(smooth) {
    scroller.scrollTo({ top: scroller.scrollHeight, behavior: smooth ? "smooth" : "auto" });
  }

  function renderUserMessage(text, animate) {
    const bubble = fromTemplate("tpl-user-message");
    bubble.querySelector("[data-text]").textContent = text;
    return addToChat(bubble, animate);
  }

  function renderAiMessage(reply, animate) {
    const bubble = fromTemplate("tpl-ai-message");
    const tickers = (reply.related_tickers || [])
      .map((ticker) => String(ticker).toUpperCase())
      .filter((ticker) => /^[A-Z]{1,5}$/.test(ticker)); // letters only, safe to put in a regex

    const paragraphBox = bubble.querySelector("[data-paragraphs]");
    reply.paragraphs.forEach((text) => {
      const paragraph = document.createElement("p");
      addFormattedText(paragraph, text, tickers);
      paragraphBox.append(paragraph);
    });

    if (reply.vocab) {
      bubble.querySelector("[data-vocab]").classList.remove("hidden");
      bubble.querySelector("[data-vocab-term]").textContent = reply.vocab.term + " —";
      bubble.querySelector("[data-vocab-definition]").textContent = reply.vocab.definition;
    }

    const copyButton = bubble.querySelector("[data-copy]");
    copyButton.addEventListener("click", () => copyReply(reply, copyButton));

    return addToChat(bubble, animate);
  }

  // Turns "**Beta** is 1.95 for TSLA" into: <strong>Beta</strong> is 1.95 for [TSLA pill]
  function addFormattedText(parent, text, tickers) {
    text.split(/(\*\*[^*]+\*\*)/g).forEach((part) => {
      if (!part) return;
      const isBold = part.length > 4 && part.startsWith("**") && part.endsWith("**");
      const content = isBold ? part.slice(2, -2) : part;

      if (isBold && !tickers.includes(content)) {
        const strong = document.createElement("strong");
        strong.className = "font-semibold text-white";
        addTextWithTickers(strong, content, tickers);
        parent.append(strong);
      } else {
        addTextWithTickers(parent, content, tickers);
      }
    });
  }

  // Adds plain text, turning any ticker symbols into clickable pills
  function addTextWithTickers(parent, text, tickers) {
    if (tickers.length === 0) {
      parent.append(text);
      return;
    }
    const tickerPattern = new RegExp(`\\b(${tickers.join("|")})\\b`, "g");
    let position = 0;
    for (const match of text.matchAll(tickerPattern)) {
      parent.append(text.slice(position, match.index), makeTickerPill(match[0]));
      position = match.index + match[0].length;
    }
    parent.append(text.slice(position));
  }

  function makeTickerPill(ticker) {
    const pill = fromTemplate("tpl-ticker");
    pill.textContent = ticker;
    pill.href = stockUrl.replace("__TICKER__", encodeURIComponent(ticker));
    pill.title = `View ${ticker} on Stock Detail`;
    return pill;
  }

  async function copyReply(reply, button) {
    const lines = [...reply.paragraphs];
    if (reply.vocab) lines.push(`${reply.vocab.term}: ${reply.vocab.definition}`);
    const plainText = lines.join("\n\n").replaceAll("**", "");

    const label = button.querySelector("[data-copy-label]");
    try {
      await navigator.clipboard.writeText(plainText);
      label.textContent = "Copied!";
    } catch {
      label.textContent = "Couldn't copy";
    }
    setTimeout(() => (label.textContent = "Copy"), 1500);
  }


  // ---------- Sending messages ----------

  function sendMessage(text) {
    text = text.trim();
    if (!text || isLoading) return;

    history.push({ role: "user", text });
    saveHistory();
    renderUserMessage(text, true);

    input.value = "";
    resizeInput();
    requestReply(text);
  }

  async function requestReply(text) {
    if (isLoading) return;
    setLoading(true);
    const typingBubble = addToChat(fromTemplate("tpl-typing"), true);

    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!response.ok) throw new Error(`Server responded with ${response.status}`);
      const reply = await response.json();

      typingBubble.remove();
      renderAiMessage(reply, true);
      history.push({ role: "ai", reply }); // saved only after it displayed correctly
      saveHistory();
    } catch (error) {
      console.error("Chat request failed:", error);
      typingBubble.remove();
      showErrorBubble(text);
    } finally {
      setLoading(false);
      // Refocus on desktop only (on phones it would pop the keyboard back up)
      if (window.matchMedia("(pointer: fine)").matches) input.focus();
    }
  }

  function showErrorBubble(text) {
    const bubble = fromTemplate("tpl-error");
    bubble.querySelector("[data-retry]").addEventListener("click", () => {
      if (isLoading) return;
      bubble.remove();
      requestReply(text);
    });
    addToChat(bubble, true);
  }


  // ---------- Page state ----------

  function setLoading(loading) {
    isLoading = loading;
    input.disabled = loading;
    promptChips.forEach((chip) => (chip.disabled = loading));
    updateLayout();
  }

  // Show the empty state or the conversation, and enable/disable buttons
  function updateLayout() {
    const isEmpty = messageList.children.length === 0;
    emptyState.classList.toggle("hidden", !isEmpty);
    messageList.classList.toggle("hidden", isEmpty);
    suggestionRow.classList.toggle("hidden", isEmpty);
    clearButton.disabled = isEmpty || isLoading;
    sendButton.disabled = isLoading || input.value.trim() === "";
  }

  // Grow the text box as the user types (up to max-h-40 from the HTML)
  function resizeInput() {
    input.style.height = "auto";
    // When empty, stay one line tall (otherwise a long placeholder would stretch it)
    if (input.value) input.style.height = `${input.scrollHeight}px`;
  }

  function clearChat() {
    history = [];
    saveHistory();
    messageList.replaceChildren();
    updateLayout();
    input.focus();
  }


  // ---------- Event listeners ----------

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage(input.value);
  });

  input.addEventListener("keydown", (event) => {
    // Enter sends, Shift+Enter adds a new line.
    // isComposing: don't send while typing with an input method (e.g. Japanese, Chinese).
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      sendMessage(input.value);
    }
  });

  input.addEventListener("input", () => {
    resizeInput();
    updateLayout();
  });

  promptChips.forEach((chip) => {
    chip.addEventListener("click", () => sendMessage(chip.dataset.prompt));
  });

  clearButton.addEventListener("click", clearChat);


  // ---------- Start up: redraw any saved conversation ----------

  try {
    history.forEach((item) => {
      if (item.role === "user") renderUserMessage(item.text, false);
      else renderAiMessage(item.reply, false);
    });
  } catch (error) {
    console.error("Saved chat couldn't be restored, starting fresh:", error);
    history = [];
    saveHistory();
    messageList.replaceChildren();
  }
  updateLayout();
  scrollToBottom(false);
})();
