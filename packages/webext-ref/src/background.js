// Background service worker (esqueleto)
chrome.webRequest.onBeforeRequest.addListener(
  function(details) {
    // Placeholder: here you'd check against rules and block or report
    return {};
  },
  {urls: ["<all_urls>"]},
  ["blocking"]
);
