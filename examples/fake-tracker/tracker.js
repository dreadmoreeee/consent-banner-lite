// "Demo Analytics": a fake tracker that behaves like a typical analytics tag.
// Served from a second local origin by examples/serve_demo.py.
(function () {
  var origin = new URL(document.currentScript.src).origin;
  var id = "DA1." + Math.floor(Math.random() * 1e9);
  window.demoTrackerRuns = (window.demoTrackerRuns || 0) + 1;
  // First-party cookie written by a third-party script (like _ga).
  document.cookie = "_da_id=" + id + "; path=/; max-age=63072000; SameSite=Lax";
  try { localStorage.setItem("_da_last_visit", String(Date.now())); } catch (e) {}
  // Beacon to the tracker's own host; its response sets a third-party cookie.
  new Image().src = origin + "/collect?cid=" + id + "&dl=" + encodeURIComponent(location.href);
})();
