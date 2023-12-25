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
