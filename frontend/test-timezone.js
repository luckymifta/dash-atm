// Test timezone conversion for Dili time
const testDates = [
  "2025-06-01T08:53:09", // retrieved_date format (UTC)
  "01:06:2025 10:51:36", // fault_data.creationDate format
  "2025-06-01T17:15:33.720676+09:00", // metadata.retrieval_timestamp format (already UTC+9)
];

console.log("Testing timezone conversion to Dili time (UTC+9):");
console.log("=".repeat(60));

testDates.forEach((dateStr, index) => {
  console.log(`\nTest ${index + 1}: ${dateStr}`);
  
  let date;
  
  if (dateStr.includes(" ") && dateStr.includes(":") && !dateStr.includes("T")) {
    // Handle "01:06:2025 10:51:36" format
    const parts = dateStr.split(' ');
    if (parts.length === 2) {
      const datePart = parts[0].split(':');
      const timePart = parts[1];
      if (datePart.length === 3) {
        // Reconstruct as YYYY-MM-DD HH:mm:ss
        const reconstructed = `${datePart[2]}-${datePart[1]}-${datePart[0]} ${timePart}`;
        console.log(`  Reconstructed: ${reconstructed}`);
        date = new Date(reconstructed);
      }
    }
  } else {
    date = new Date(dateStr);
  }
  
  if (date && !isNaN(date.getTime())) {
    console.log(`  UTC Date: ${date.toISOString()}`);
    console.log(`  Dili Date: ${date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'Asia/Dili'
    })}`);
    console.log(`  Dili Time: ${date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Dili'
    })}`);
  } else {
    console.log(`  ERROR: Invalid date`);
  }
});

console.log("\n" + "=".repeat(60));
console.log("Current time in different timezones:");
const now = new Date();
console.log(`UTC: ${now.toISOString()}`);
console.log(`Dili (UTC+9): ${now.toLocaleString('en-US', { timeZone: 'Asia/Dili' })}`);
