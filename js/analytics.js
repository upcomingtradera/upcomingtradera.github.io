// Initialize Google Analytics (replace 'UA-XXXXX-Y' with your tracking ID)
ga('create', googleAnalyticsCode, 'auto');

// Function to send interaction data to Google Analytics
function trackInteraction(type, x, y) {
  ga('send', 'event', type, 'interact', `x:${x}, y:${y}`);
}

// Function to handle mouse movements
function handleMouseMove(e) {
  trackInteraction('Mouse Movement', e.clientX, e.clientY);
}

// Function to handle clicks
function handleClick(e) {
  trackInteraction('Mouse Click', e.clientX, e.clientY);
}

// Function to handle touch events
function handleTouch(e) {
  const touch = e.touches[0];
  trackInteraction('Touch', touch.clientX, touch.clientY);
}

// Attach event listeners
document.addEventListener('mousemove', handleMouseMove);
document.addEventListener('click', handleClick);
document.addEventListener('touchstart', handleTouch);

