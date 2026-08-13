(function () {
  "use strict";

  var platform = window.MagicMapperPlatform;
  var state = { status: null, sourceButton: null, modal: null, busy: false };
  var buttonLabels = {
    prime: "Prime Video", netflix: "Netflix", disney: "Disney+", rakuten: "Rakuten TV",
    alexa: "Alexa", google: "Google Assistant", lg_channels: "LG Channels", ch_up: "Channel up",
    ch_down: "Channel down", vol_up: "Volume up", vol_down: "Volume down", fastforward: "Fast-forward",
    channels_alt: "Channels", search_alt: "Search", "...": "More actions", "...alt": "More actions"
  };

  var elements = {
    statusDot: document.getElementById("status-dot"), statusLabel: document.getElementById("status-label"),
    summary: document.getElementById("summary"), count: document.getElementById("mapping-count"),
    primary: document.getElementById("primary-button"), discover: document.getElementById("discover-button"),
    mappings: document.getElementById("mappings"), empty: document.getElementById("empty-state"),
    modal: document.getElementById("modal"), modalCard: document.getElementById("modal-card"),
    system: document.getElementById("system-button"), toast: document.getElementById("toast")
  };

  function label(button) {
    return buttonLabels[button] || button.replace(/_/g, " ").replace(/(^|\s)\S/g, function (letter) { return letter.toUpperCase(); });
  }

  function describe(action) {
    if (action === "disabled") return "Disabled — default action blocked";
    if (Array.isArray(action)) return action.length + " actions";
    if (!action) return "Unchanged";
    if (action.function === "launch_app") return "Opens " + (action.inputs.app_title || action.inputs.app_id);
    if (action.function === "press_button") return "Acts like " + label(action.inputs.button);
    return action.function.replace(/_/g, " ");
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character];
    });
  }

  function setBusy(busy) {
    state.busy = busy;
    document.body.classList.toggle("is-busy", busy);
  }

  function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.hidden = false;
    window.clearTimeout(showToast.timeout);
    showToast.timeout = window.setTimeout(function () { elements.toast.hidden = true; }, 2600);
  }

  function render() {
    var status = state.status || { active: false, installed: false, config: {} };
    var config = status.config || {};
    var entries = Object.keys(config).sort();
    elements.statusDot.classList.toggle("active", Boolean(status.active));
    elements.statusLabel.textContent = status.active ? "Active now" : (status.installed ? "Stopped" : "Not set up");
    elements.count.textContent = entries.length;
    elements.summary.textContent = status.active
      ? "The mapper has exclusive control of the remote. Unchanged buttons pass straight through to webOS."
      : (status.installed ? "Your map is saved, but the remote service is stopped." : "Set up the local service once, then reclaim buttons without editing files or restarting the TV.");
    elements.primary.textContent = !status.installed ? "Set up Magic Mapper" : (status.active ? "Discover another button" : "Start mapper");
    elements.discover.disabled = !status.active;
    elements.empty.hidden = entries.length > 0;
    elements.mappings.innerHTML = entries.map(function (button) {
      return '<div class="mapping-row"><span class="key-name">' + escapeHtml(label(button)) + '</span>' +
        '<span class="mapping-action">' + escapeHtml(describe(config[button])) + '</span>' +
        '<button class="row-action focusable" type="button" data-remove="' + escapeHtml(button) + '">Restore</button></div>';
    }).join("");
    bindDynamicActions();
  }

  function refresh() {
    return platform.status().then(function (response) {
      state.status = response.status;
      render();
      return response.status;
    }).catch(showError);
  }

  function primaryAction() {
    if (!state.status || !state.status.installed) {
      setBusy(true);
      platform.install().then(function (response) {
        state.status = response.status;
        render();
        showToast(response.migrated ? "Existing mappings imported" : "Magic Mapper is active");
      }).catch(showError).finally(function () { setBusy(false); });
    } else if (!state.status.active) {
      setBusy(true);
      platform.start().then(refresh).then(function () { showToast("Mapper started"); }).finally(function () { setBusy(false); });
    } else startDiscovery("source");
  }

  function startDiscovery(purpose) {
    if (!state.status || !state.status.active || state.busy) return;
    var requestId = String(Date.now()) + "-" + Math.floor(Math.random() * 10000);
    openModal('<p class="eyebrow">BUTTON DISCOVERY</p><h2>' + (purpose === "target" ? "Press the target button" : "Press one remote button") + '</h2>' +
      '<p class="modal-copy">' + (purpose === "target" ? "The first button will behave like this one." : "Its normal action will be blocked while we identify it.") + '</p>' +
      '<div class="discovery-signal">···</div><p class="modal-copy">Waiting for a complete press…</p>', "narrow", false);
    platform.discover(requestId).then(function () { pollDiscovery(requestId, purpose, 0); }).catch(showError);
  }

  function pollDiscovery(requestId, purpose, attempts) {
    window.setTimeout(function () {
      platform.discoveryResult(requestId).then(function (result) {
        if (result.pending && attempts < 28) return pollDiscovery(requestId, purpose, attempts + 1);
        if (!result.ok) throw new Error(result.error || "No button was detected");
        if (result.pending) throw new Error("No button was detected");
        if (String(result.button).indexOf("code_") === 0) throw new Error("That button is not supported yet (code " + result.code + ")");
        if (purpose === "target") return applyMapping(state.sourceButton, { function: "press_button", inputs: { button: result.button } });
        state.sourceButton = result.button;
        showActionChoices(result.button);
      }).catch(showError);
    }, 450);
  }

  function showActionChoices(button) {
    openModal('<p class="eyebrow">' + escapeHtml(label(button).toUpperCase()) + ' FOUND</p><h2>What should it do?</h2>' +
      '<p class="modal-copy">This replaces the button’s built-in action.</p><div class="choices">' +
      '<button class="choice focusable" type="button" data-action="disable"><strong>Disable it</strong><span>Block the branded shortcut completely.</span></button>' +
      '<button class="choice focusable" type="button" data-action="app"><strong>Open an app</strong><span>Choose from apps installed on this TV.</span></button>' +
      '<button class="choice focusable" type="button" data-action="remap"><strong>Act like another button</strong><span>Press a second remote button to copy it.</span></button></div>');
  }

  function showApps() {
    openModal('<p class="eyebrow">CHOOSE DESTINATION</p><h2>Open an app</h2><p class="modal-copy">Loading the apps installed on this TV…</p>', "", false);
    platform.apps().then(function (response) {
      var apps = response.apps || [];
      elements.modalCard.innerHTML = '<p class="eyebrow">CHOOSE DESTINATION</p><h2>Open an app</h2>' +
        '<div class="app-list">' + apps.map(function (app) {
          return '<button class="app-option focusable" type="button" data-app-id="' + escapeHtml(app.id) + '" data-app-title="' + escapeHtml(app.title) + '"><span>' + escapeHtml(app.title) + '</span><small>' + escapeHtml(app.id) + '</small></button>';
        }).join("") + '</div><div class="modal-actions"><button class="secondary focusable" data-close type="button">Cancel</button></div>';
      bindDynamicActions(); focusFirst();
    }).catch(showError);
  }

  function applyMapping(button, action) {
    var config = Object.assign({}, state.status.config || {});
    config[button] = action;
    setBusy(true);
    platform.configure(config).then(function (response) {
      state.status = response.status;
      closeModal(); render(); showToast(label(button) + " updated and active");
    }).catch(showError).finally(function () { setBusy(false); });
  }

  function removeMapping(button) {
    var config = Object.assign({}, state.status.config || {});
    delete config[button];
    setBusy(true);
    platform.configure(config).then(function (response) {
      state.status = response.status; render(); showToast(label(button) + " restored");
    }).catch(showError).finally(function () { setBusy(false); });
  }

  function showSystem() {
    var active = state.status && state.status.active;
    openModal('<p class="eyebrow">LOCAL SERVICE</p><h2>Service &amp; removal</h2>' +
      '<p class="modal-copy">The mapper runs entirely on this TV and starts with webOS.</p>' +
      '<button class="service-row focusable" data-service="toggle" type="button"><span>' + (active ? "Stop mapper" : "Start mapper") + '</span><span>→</span></button>' +
      '<button class="service-row focusable" data-service="logs" type="button"><span>View recent log</span><span>→</span></button>' +
      '<button class="service-row focusable" data-service="uninstall" type="button"><span>Uninstall Magic Mapper</span><span>→</span></button>' +
      '<div class="modal-actions"><button class="secondary focusable" data-close type="button">Done</button></div>');
  }

  function showLogs() {
    platform.logs().then(function (response) {
      openModal('<p class="eyebrow">RECENT LOG</p><h2>What the mapper sees</h2><pre class="log">' + escapeHtml(response.log || "No log yet.") + '</pre>' +
        '<div class="modal-actions"><button class="secondary focusable" data-close type="button">Done</button></div>');
    }).catch(showError);
  }

  function confirmUninstall() {
    openModal('<p class="eyebrow">UNINSTALL</p><h2>Remove everything?</h2><p class="modal-copy">This stops the mapper, restores every remote button, removes your mappings and uninstalls this app.</p>' +
      '<div class="modal-actions"><button class="confirm danger focusable" data-confirm-uninstall type="button">Uninstall</button><button class="secondary focusable" data-close type="button">Keep it</button></div>', "narrow");
  }

  function openModal(html, extraClass, closable) {
    state.modal = true;
    elements.modalCard.className = "modal-card " + (extraClass || "");
    elements.modalCard.innerHTML = html;
    elements.modal.hidden = false;
    elements.modal.dataset.closable = closable === false ? "false" : "true";
    bindDynamicActions(); focusFirst();
  }

  function closeModal() {
    state.modal = null;
    elements.modal.hidden = true;
    elements.modalCard.innerHTML = "";
    elements.discover.focus();
  }

  function showError(error) {
    setBusy(false);
    openModal('<p class="eyebrow">COULD NOT COMPLETE</p><h2>Something got in the way.</h2><p class="modal-copy">' + escapeHtml(error.message || error) + '</p>' +
      '<div class="modal-actions"><button class="secondary focusable" data-close type="button">Back</button></div>', "narrow");
  }

  function bindDynamicActions() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-remove]"), function (button) { button.onclick = function () { removeMapping(button.dataset.remove); }; });
    Array.prototype.forEach.call(document.querySelectorAll("[data-close]"), function (button) { button.onclick = closeModal; });
    Array.prototype.forEach.call(document.querySelectorAll("[data-action]"), function (button) {
      button.onclick = function () {
        if (button.dataset.action === "disable") applyMapping(state.sourceButton, "disabled");
        if (button.dataset.action === "app") showApps();
        if (button.dataset.action === "remap") startDiscovery("target");
      };
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-app-id]"), function (button) {
      button.onclick = function () { applyMapping(state.sourceButton, { function: "launch_app", inputs: { app_id: button.dataset.appId, app_title: button.dataset.appTitle } }); };
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-service]"), function (button) {
      button.onclick = function () {
        if (button.dataset.service === "toggle") {
          var action = state.status.active ? platform.stop() : platform.start();
          setBusy(true); action.then(refresh).then(closeModal).finally(function () { setBusy(false); });
        }
        if (button.dataset.service === "logs") showLogs();
        if (button.dataset.service === "uninstall") confirmUninstall();
      };
    });
    var confirm = document.querySelector("[data-confirm-uninstall]");
    if (confirm) confirm.onclick = function () { setBusy(true); platform.uninstall().then(function () { closeModal(); showToast("Magic Mapper removed"); }).catch(showError); };
  }

  function focusFirst() {
    window.setTimeout(function () {
      var first = elements.modalCard.querySelector(".focusable");
      if (first) first.focus();
    }, 0);
  }

  function moveFocus(direction) {
    var scope = state.modal ? elements.modalCard : document;
    var candidates = Array.prototype.filter.call(scope.querySelectorAll(".focusable"), function (item) { return !item.disabled && item.offsetParent !== null; });
    var current = document.activeElement;
    if (candidates.indexOf(current) < 0) { if (candidates[0]) candidates[0].focus(); return; }
    var from = current.getBoundingClientRect();
    var originX = from.left + from.width / 2, originY = from.top + from.height / 2;
    var best = null, bestScore = Infinity;
    candidates.forEach(function (candidate) {
      if (candidate === current) return;
      var box = candidate.getBoundingClientRect();
      var dx = box.left + box.width / 2 - originX, dy = box.top + box.height / 2 - originY;
      if ((direction === "left" && dx >= -4) || (direction === "right" && dx <= 4) || (direction === "up" && dy >= -4) || (direction === "down" && dy <= 4)) return;
      var primary = direction === "left" || direction === "right" ? Math.abs(dx) : Math.abs(dy);
      var secondary = direction === "left" || direction === "right" ? Math.abs(dy) : Math.abs(dx);
      var score = primary + secondary * 2.2;
      if (score < bestScore) { bestScore = score; best = candidate; }
    });
    if (best) {
      best.focus();
      best.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }

  document.addEventListener("keydown", function (event) {
    var directions = { 37: "left", 38: "up", 39: "right", 40: "down" };
    if (directions[event.keyCode]) { event.preventDefault(); moveFocus(directions[event.keyCode]); }
    if ((event.keyCode === 461 || event.keyCode === 27) && state.modal && elements.modal.dataset.closable !== "false") { event.preventDefault(); closeModal(); }
  });

  elements.primary.onclick = primaryAction;
  elements.discover.onclick = function () { startDiscovery("source"); };
  elements.system.onclick = showSystem;
  refresh().then(function () { elements.primary.focus(); });
}());
