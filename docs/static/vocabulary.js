// SPDX-FileCopyrightText: mathspec contributors
//
// SPDX-License-Identifier: MIT

// The viewer of `docs/vocabulary.md`. It reads the tables the page already
// holds and colours them, so the Markdown stays the one place a word is
// written: a row with a `Status` cell colours its three words by that status,
// and a row without one colours a meaning by whether another package states
// it in the same words. The page opts in with an element whose id is
// `vocabulary-filter`, which also receives the filter buttons.
(function () {
  const PACKAGES = ["mathspec", "specsolve", "datarecord"];
  const STATUSES = [
    ["🔴", "mismatch", "Mismatch"],
    ["🟢", "aligned", "Aligned"],
    ["🔵", "apart", "Kept apart"],
    ["⚪", "single", "One package only"],
  ];
  const STYLE = `
    :root, [data-md-color-scheme="default"] {
      --vocabulary-mismatch-bg: #fcdedc; --vocabulary-mismatch-fg: #8c1d18;
      --vocabulary-aligned-bg: #dcf2e2; --vocabulary-aligned-fg: #14532d;
      --vocabulary-apart-bg: #e3e7f8; --vocabulary-apart-fg: #2b3580;
      --vocabulary-single-bg: #edf0f3; --vocabulary-single-fg: #3d4956;
    }
    [data-md-color-scheme="slate"] {
      --vocabulary-mismatch-bg: #4b1b1e; --vocabulary-mismatch-fg: #ffb4b0;
      --vocabulary-aligned-bg: #133523; --vocabulary-aligned-fg: #9fe5b7;
      --vocabulary-apart-bg: #222a57; --vocabulary-apart-fg: #c4caff;
      --vocabulary-single-bg: #1f2832; --vocabulary-single-fg: #c3ccd6;
    }
    td.vocabulary-mismatch { background: var(--vocabulary-mismatch-bg); color: var(--vocabulary-mismatch-fg); }
    td.vocabulary-aligned { background: var(--vocabulary-aligned-bg); color: var(--vocabulary-aligned-fg); }
    td.vocabulary-apart { background: var(--vocabulary-apart-bg); color: var(--vocabulary-apart-fg); }
    td.vocabulary-single { background: var(--vocabulary-single-bg); color: var(--vocabulary-single-fg); }
    td[class^="vocabulary-"] code { background: transparent; color: inherit; }
    #vocabulary-filter { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.8rem 0; }
    #vocabulary-filter button {
      font: inherit; font-size: 0.7rem; cursor: pointer; padding: 0.2rem 0.7rem; border-radius: 1rem;
      color: var(--md-default-fg-color); background: var(--md-default-bg-color);
      border: 1px solid var(--md-default-fg-color--lighter);
    }
    #vocabulary-filter button[aria-pressed="true"] { border-color: var(--md-default-fg-color); font-weight: 700; }
  `;

  function columns(table) {
    const names = Array.from(table.querySelectorAll("thead th"), (th) => th.textContent.trim());
    return { words: PACKAGES.map((name) => names.indexOf(name)), status: names.indexOf("Status") };
  }

  function statusOf(text) {
    const found = STATUSES.find(([mark]) => text.includes(mark));
    return found ? found[1] : null;
  }

  function paintByStatus(row, words, status) {
    const kind = statusOf(row.cells[status].textContent);
    if (!kind) return;
    row.dataset.vocabulary = kind;
    for (const index of words) {
      if (row.cells[index].textContent.trim()) row.cells[index].classList.add(`vocabulary-${kind}`);
    }
  }

  function paintByAgreement(row, words) {
    const texts = words.map((index) => row.cells[index].textContent.trim());
    words.forEach((index, at) => {
      if (!texts[at]) return;
      const shared = texts.some((other, where) => where !== at && other === texts[at]);
      row.cells[index].classList.add(shared ? "vocabulary-aligned" : "vocabulary-mismatch");
    });
  }

  function addFilter(mount, rows) {
    const show = (kind) => {
      for (const row of rows) row.hidden = kind !== "all" && row.dataset.vocabulary !== kind;
      for (const button of mount.children) button.setAttribute("aria-pressed", String(button.dataset.kind === kind));
    };
    const choices = [["", "all", "All rows"], ...STATUSES];
    for (const [mark, kind, label] of choices) {
      const count = kind === "all" ? rows.length : rows.filter((row) => row.dataset.vocabulary === kind).length;
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.kind = kind;
      button.textContent = `${mark} ${label} (${count})`.trim();
      button.addEventListener("click", () => show(kind));
      mount.append(button);
    }
    show("all");
  }

  function paint() {
    const mount = document.getElementById("vocabulary-filter");
    if (!mount || mount.dataset.ready) return;
    mount.dataset.ready = "true";
    if (!document.getElementById("vocabulary-style")) {
      const style = document.createElement("style");
      style.id = "vocabulary-style";
      style.textContent = STYLE;
      document.head.append(style);
    }
    const filtered = [];
    for (const table of (mount.closest(".md-content") || document).querySelectorAll("table")) {
      const { words, status } = columns(table);
      if (words.includes(-1)) continue;
      for (const row of table.tBodies[0].rows) {
        if (status === -1) {
          paintByAgreement(row, words);
        } else {
          paintByStatus(row, words, status);
          filtered.push(row);
        }
      }
    }
    addFilter(mount, filtered);
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(paint);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", paint);
  } else {
    paint();
  }
})();
