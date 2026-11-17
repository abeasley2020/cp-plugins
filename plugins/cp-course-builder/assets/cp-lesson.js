/* cp-lesson.js: behavior for cp-course-builder pages.
   Every component is complete without this file. It only adds behavior:
   accordion and tab keyboard patterns, the step-by-step process, checking
   answers, and SCORM 1.2 completion when the page runs inside an LMS.
   Nothing is stored: no cookies, no local storage, no network calls. */
(function () {
  "use strict";
  var doc = document;
  var all = function (sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); };
  var uid = 0;
  var nextId = function (p) { uid += 1; return "cp-" + p + "-" + uid; };

  /* Accordion: WAI-ARIA accordion pattern. Panels open independently. */
  all("[data-cp-accordion]").forEach(function (group) {
    var heads = all(".cp-acc-h", group);
    heads.forEach(function (h) {
      var panel = h.nextElementSibling;
      if (!panel || !panel.classList.contains("cp-acc-panel")) return;
      var btn = doc.createElement("button");
      btn.type = "button";
      btn.innerHTML = h.innerHTML;
      btn.setAttribute("aria-expanded", "false");
      panel.id = panel.id || nextId("panel");
      btn.id = nextId("acc");
      btn.setAttribute("aria-controls", panel.id);
      panel.setAttribute("role", "region");
      panel.setAttribute("aria-labelledby", btn.id);
      panel.hidden = true;
      h.innerHTML = "";
      h.appendChild(btn);
      btn.addEventListener("click", function () {
        var open = btn.getAttribute("aria-expanded") === "true";
        btn.setAttribute("aria-expanded", String(!open));
        panel.hidden = open;
      });
      btn.addEventListener("keydown", function (e) {
        var btns = heads.map(function (x) { return x.querySelector("button"); });
        var i = btns.indexOf(btn);
        var t = null;
        if (e.key === "ArrowDown") t = btns[(i + 1) % btns.length];
        else if (e.key === "ArrowUp") t = btns[(i - 1 + btns.length) % btns.length];
        else if (e.key === "Home") t = btns[0];
        else if (e.key === "End") t = btns[btns.length - 1];
        if (t) { e.preventDefault(); t.focus(); }
      });
    });
  });

  /* Tabs: WAI-ARIA tabs with roving tabindex and automatic activation. */
  all("[data-cp-tabs]").forEach(function (box) {
    var panels = all(".cp-tab-panel", box);
    if (panels.length < 2) return;
    var list = doc.createElement("div");
    list.className = "cp-tablist";
    list.setAttribute("role", "tablist");
    list.setAttribute("aria-label", box.getAttribute("data-label") || "Options");
    var tabs = panels.map(function (p, i) {
      var head = p.querySelector(".cp-tab-h");
      var t = doc.createElement("button");
      t.type = "button";
      t.setAttribute("role", "tab");
      t.id = nextId("tab");
      t.textContent = head ? head.textContent : "Option " + (i + 1);
      t.setAttribute("aria-controls", p.id);
      p.setAttribute("role", "tabpanel");
      p.setAttribute("aria-labelledby", t.id);
      p.tabIndex = 0;
      list.appendChild(t);
      return t;
    });
    function select(i, focus) {
      tabs.forEach(function (t, j) {
        var on = i === j;
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        panels[j].hidden = !on;
      });
      if (focus) tabs[i].focus();
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(i); });
      t.addEventListener("keydown", function (e) {
        var n = tabs.length, k = null;
        if (e.key === "ArrowRight") k = (i + 1) % n;
        else if (e.key === "ArrowLeft") k = (i - 1 + n) % n;
        else if (e.key === "Home") k = 0;
        else if (e.key === "End") k = n - 1;
        if (k !== null) { e.preventDefault(); select(k, true); }
      });
    });
    box.insertBefore(list, box.firstChild);
    box.classList.add("cp-enhanced");
    select(0);
  });

  /* Process: one step at a time with Previous and Next. */
  all("[data-cp-process]").forEach(function (ol) {
    var steps = all(".cp-step", ol);
    if (steps.length < 2) return;
    var i = 0;
    var nav = doc.createElement("div");
    nav.className = "cp-step-nav";
    var count = doc.createElement("p");
    count.className = "cp-step-count";
    count.setAttribute("aria-live", "polite");
    var prev = doc.createElement("button");
    prev.type = "button"; prev.className = "cp-btn cp-btn-quiet"; prev.textContent = "Previous step";
    var next = doc.createElement("button");
    next.type = "button"; next.className = "cp-btn"; next.textContent = "Next step";
    var allBtn = doc.createElement("button");
    allBtn.type = "button"; allBtn.className = "cp-btn cp-btn-quiet"; allBtn.textContent = "Show all steps";
    nav.appendChild(count); nav.appendChild(prev); nav.appendChild(next); nav.appendChild(allBtn);
    ol.parentNode.insertBefore(nav, ol.nextSibling);
    ol.classList.add("cp-enhanced");
    function show() {
      steps.forEach(function (s, j) { s.hidden = j !== i; });
      count.textContent = "Step " + (i + 1) + " of " + steps.length;
      prev.disabled = i === 0;
      next.disabled = i === steps.length - 1;
    }
    prev.addEventListener("click", function () { if (i > 0) { i -= 1; show(); } });
    next.addEventListener("click", function () { if (i < steps.length - 1) { i += 1; show(); } });
    allBtn.addEventListener("click", function () {
      steps.forEach(function (s) { s.hidden = false; });
      ol.classList.remove("cp-enhanced");
      nav.parentNode.removeChild(nav);
    });
    show();
  });

  /* Knowledge checks and scenarios: feedback for every chosen option. */
  all("[data-cp-check]").forEach(function (form) {
    var actions = form.querySelector(".cp-actions");
    var status = form.querySelector(".cp-status");
    var key = form.querySelector(".cp-key");
    var scenario = form.getAttribute("data-kind") === "scenario";
    if (actions) actions.hidden = false;
    if (key) key.hidden = true;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var inputs = all("input", form);
      var chosen = inputs.filter(function (x) { return x.checked; });
      all(".cp-feedback", form).forEach(function (f) { f.hidden = true; f.className = "cp-feedback"; });
      if (!chosen.length) { status.textContent = "Choose an answer first."; return; }
      var right = inputs.every(function (x) { return x.checked === (x.getAttribute("data-correct") === "true"); });
      chosen.forEach(function (x) {
        var f = form.querySelector('.cp-feedback[data-for="' + x.id + '"]');
        if (!f) return;
        f.hidden = false;
        f.classList.add(x.getAttribute("data-correct") === "true" ? "cp-is-ok" : "cp-is-no");
      });
      if (!right) {
        inputs.forEach(function (x) {
          if (x.type === "checkbox" && x.getAttribute("data-correct") === "true" && !x.checked) {
            var f = form.querySelector('.cp-feedback[data-for="' + x.id + '"]');
            if (f) { f.hidden = false; f.classList.add("cp-is-no"); f.querySelector("strong").textContent = "You missed this one."; }
          }
        });
      }
      status.textContent = scenario ? "Read what happens next to your choice." :
        (right ? "Correct. Read why below each choice." : "Not yet. Read the feedback under your choices, then try again.");
      if (key) key.hidden = false;
    });
    form.addEventListener("reset", function () {
      all(".cp-feedback", form).forEach(function (f) { f.hidden = true; });
      status.textContent = "";
      if (key) key.hidden = true;
    });
  });

  /* Sorting: each item has a select; feedback names the right category. */
  all("[data-cp-sort]").forEach(function (form) {
    var actions = form.querySelector(".cp-actions");
    var status = form.querySelector(".cp-status");
    var key = form.querySelector(".cp-key");
    if (actions) actions.hidden = false;
    if (key) key.hidden = true;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var sels = all("select", form), right = 0;
      sels.forEach(function (s) {
        var f = form.querySelector('.cp-feedback[data-for="' + s.id + '"]');
        var ok = s.selectedOptions[0] && s.selectedOptions[0].getAttribute("data-correct") === "true";
        var answer = all("option", s).filter(function (o) { return o.getAttribute("data-correct") === "true"; })[0];
        if (ok) right += 1;
        if (f) {
          f.hidden = false;
          f.innerHTML = "";
          var strong = doc.createElement("strong");
          strong.textContent = ok ? "Correct." : "Not this one.";
          f.appendChild(strong);
          f.appendChild(doc.createTextNode(" It belongs in " + (answer ? answer.textContent : "another category") + "."));
          f.className = "cp-feedback " + (ok ? "cp-is-ok" : "cp-is-no");
        }
      });
      status.textContent = right + " of " + sels.length + " sorted correctly.";
      if (key) key.hidden = false;
    });
    form.addEventListener("reset", function () {
      all(".cp-feedback", form).forEach(function (f) { f.hidden = true; });
      status.textContent = "";
      if (key) key.hidden = true;
    });
  });

  /* Print: open every disclosure so nothing is lost on paper. */
  window.addEventListener("beforeprint", function () {
    all("details").forEach(function (d) { d.setAttribute("data-was-open", d.open ? "1" : "0"); d.open = true; });
  });
  window.addEventListener("afterprint", function () {
    all("details[data-was-open]").forEach(function (d) { d.open = d.getAttribute("data-was-open") === "1"; });
  });

  /* SCORM 1.2: incomplete on load, completed when the end of the lesson is reached. */
  function findAPI(win) {
    var tries = 0;
    while (win && tries < 10) {
      if (win.API) return win.API;
      if (win.parent === win) break;
      win = win.parent; tries += 1;
    }
    return null;
  }
  var api = null;
  try { api = findAPI(window) || (window.opener && findAPI(window.opener)); } catch (err) { api = null; }
  if (api && api.LMSInitialize("") === "true") {
    var done = false;
    var status = api.LMSGetValue("cmi.core.lesson_status");
    if (status === "not attempted" || status === "") { api.LMSSetValue("cmi.core.lesson_status", "incomplete"); api.LMSCommit(""); }
    var complete = function () {
      if (done) return;
      done = true;
      api.LMSSetValue("cmi.core.lesson_status", "completed");
      api.LMSCommit("");
    };
    var end = doc.getElementById("cp-end");
    if (end && "IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) complete(); });
      }).observe(end);
    }
    var finished = false;
    var finish = function () { if (finished) return; finished = true; api.LMSCommit(""); api.LMSFinish(""); };
    window.addEventListener("pagehide", finish);
    window.addEventListener("beforeunload", finish);
  }
})();
