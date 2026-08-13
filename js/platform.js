(function () {
  "use strict";

  var APP_DIR = "/media/developer/apps/usr/palm/applications/com.github.andrewfraley.magicmapper";
  var CONTROLLER = "/usr/bin/python3 " + APP_DIR + "/mapperctl.py";

  function parseControllerOutput(response) {
    var stdout = response && (response.stdoutString || response.stdout || response.output || "");
    if (typeof stdout !== "string") return response;
    var lines = stdout.trim().split("\n");
    for (var index = lines.length - 1; index >= 0; index -= 1) {
      try { return JSON.parse(lines[index]); } catch (error) { /* keep looking */ }
    }
    throw new Error((response && (response.stderrString || response.stderr)) || "Magic Mapper did not return a response");
  }

  function lunaCall(uri, parameters) {
    return new Promise(function (resolve, reject) {
      var bridge = new window.PalmServiceBridge();
      var settled = false;
      var timeout = window.setTimeout(function () {
        if (!settled) reject(new Error("The TV service took too long to respond"));
      }, 15000);
      bridge.onservicecallback = function (raw) {
        if (settled) return;
        settled = true;
        window.clearTimeout(timeout);
        try {
          var response = JSON.parse(raw);
          if (response.returnValue === false) reject(new Error(response.errorText || "TV service call failed"));
          else resolve(response);
        } catch (error) { reject(error); }
      };
      bridge.call(uri, JSON.stringify(parameters || {}));
    });
  }

  function run(command, value) {
    var fullCommand = CONTROLLER + " " + command;
    if (value) fullCommand += " " + value;
    return lunaCall("luna://org.webosbrew.hbchannel.service/exec", { command: fullCommand })
      .then(parseControllerOutput)
      .then(function (response) {
        if (!response.ok) throw new Error(response.error || "Magic Mapper command failed");
        return response;
      });
  }

  function mockPlatform() {
    var stored = window.localStorage.getItem("magic-mapper-demo-config");
    var config = stored ? JSON.parse(stored) : {
      netflix: "disabled",
      prime: { function: "launch_app", inputs: { app_id: "cdp-30", app_title: "Plex" } },
      alexa: "disabled"
    };
    var active = true;
    var installed = true;
    var discoveries = ["rakuten", "disney", "netflix"];

    return {
      isMock: true,
      status: function () { return Promise.resolve({ status: { active: active, installed: installed, config: config, configDigest: "demo12345678" } }); },
      install: function () { installed = true; active = true; return this.status(); },
      start: function () { active = true; return this.status(); },
      stop: function () { active = false; return this.status(); },
      configure: function (nextConfig) {
        config = nextConfig;
        window.localStorage.setItem("magic-mapper-demo-config", JSON.stringify(config));
        return this.status();
      },
      discover: function (id) {
        window.setTimeout(function () {
          window.localStorage.setItem("magic-mapper-discovery-" + id, discoveries.shift() || "blue");
        }, 1600);
        return Promise.resolve({ ok: true });
      },
      discoveryResult: function (id) {
        var button = window.localStorage.getItem("magic-mapper-discovery-" + id);
        return Promise.resolve(button ? { ok: true, button: button, code: 1000 } : { ok: true, pending: true });
      },
      apps: function () { return Promise.resolve({ apps: [
        { id: "cdp-30", title: "Plex" }, { id: "com.webos.app.browser", title: "Web Browser" },
        { id: "youtube.leanback.v4", title: "YouTube" }, { id: "com.webos.app.hdmi1", title: "HDMI 1" }
      ] }); },
      logs: function () { return Promise.resolve({ log: "Starting Magic Mapper\nEXCLUSIVE_MODE is enabled\nFirst loop complete, Magic Mapper is running" }); },
      uninstall: function () { installed = false; active = false; config = {}; return Promise.resolve({ ok: true }); }
    };
  }

  if (!window.PalmServiceBridge) {
    window.MagicMapperPlatform = mockPlatform();
    return;
  }

  window.MagicMapperPlatform = {
    isMock: false,
    status: function () { return run("status"); },
    install: function () { return run("install"); },
    start: function () { return run("start"); },
    stop: function () { return run("stop"); },
    configure: function (config) {
      var encoded = window.btoa(unescape(encodeURIComponent(JSON.stringify(config))));
      return run("configure", encoded);
    },
    discover: function (id) { return run("discover", id); },
    discoveryResult: function (id) { return run("discovery-result", id); },
    apps: function () { return run("apps"); },
    logs: function () { return run("logs"); },
    uninstall: function () { return run("uninstall"); }
  };
}());
