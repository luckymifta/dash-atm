// Test the chart timezone conversion logic
console.log("Testing chart timezone conversion for Dili time (UTC+9):");
console.log("=".repeat(60));

// This mirrors the formatTimeForPeriod function from ATMAvailabilityChart.tsx
const formatTimeForPeriod = (date, hours) => {
  if (hours <= 24) {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Dili'
    });
  } else if (hours <= 168) {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Dili'
    });
  } else {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      timeZone: 'Asia/Dili'
    });
  }
};

// Test with various timestamps
const testTimestamps = [
  "2025-01-14T09:00:00Z",  // 9 AM UTC = 6 PM Dili
  "2025-01-14T15:30:00Z",  // 3:30 PM UTC = 12:30 AM next day Dili
  "2025-01-14T00:00:00Z",  // Midnight UTC = 9 AM Dili
];

console.log("\nTesting 24-hour format (hours <= 24):");
testTimestamps.forEach(timestamp => {
  const date = new Date(timestamp);
  const formatted = formatTimeForPeriod(date, 24);
  console.log(`UTC: ${timestamp} -> Dili: ${formatted}`);
  console.log(`  Full Dili time: ${date.toLocaleString('en-US', { timeZone: 'Asia/Dili' })}`);
});

console.log("\nTesting 7-day format (24 < hours <= 168):");
testTimestamps.forEach(timestamp => {
  const date = new Date(timestamp);
  const formatted = formatTimeForPeriod(date, 168);
  console.log(`UTC: ${timestamp} -> Dili: ${formatted}`);
});

console.log("\nTesting 30-day format (hours > 168):");
testTimestamps.forEach(timestamp => {
  const date = new Date(timestamp);
  const formatted = formatTimeForPeriod(date, 720);
  console.log(`UTC: ${timestamp} -> Dili: ${formatted}`);
});

console.log("\n" + "=".repeat(60));
console.log("Current time comparison:");
const now = new Date();
console.log(`Current UTC: ${now.toISOString()}`);
console.log(`Current Dili: ${now.toLocaleString('en-US', { timeZone: 'Asia/Dili' })}`);
console.log(`Chart format (24h): ${formatTimeForPeriod(now, 24)}`);
console.log(`Chart format (7d): ${formatTimeForPeriod(now, 168)}`);
console.log(`Chart format (30d): ${formatTimeForPeriod(now, 720)}`);
