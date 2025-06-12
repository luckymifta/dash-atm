// Test to demonstrate double timezone conversion issue
console.log("=".repeat(60));
console.log("DOUBLE TIMEZONE CONVERSION ISSUE ANALYSIS");
console.log("=".repeat(60));

// Simulate what happens in the backend
function simulateBackendConversion() {
    // Example: Database has UTC time 2025-06-12T07:50:00Z
    const utcTime = new Date('2025-06-12T07:50:00Z');
    console.log("1. Database UTC time:", utcTime.toISOString());
    
    // Backend converts to Dili time (UTC+9) and returns as timezone-naive string
    const diliTime = new Date(utcTime.getTime() + (9 * 60 * 60 * 1000));
    const backendResponse = diliTime.toISOString().replace('Z', ''); // Remove Z to make it timezone-naive
    console.log("2. Backend response (Dili time as naive):", backendResponse);
    
    return backendResponse;
}

// Simulate what happens in the frontend
function simulateFrontendConversion(backendTimestamp) {
    // Frontend receives the timestamp and creates a Date object
    const frontendDate = new Date(backendTimestamp);
    console.log("3. Frontend Date object:", frontendDate.toISOString());
    
    // Frontend applies timezone conversion AGAIN
    const frontendDisplay = frontendDate.toLocaleString('en-US', { 
        timeZone: 'Asia/Dili',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });
    console.log("4. Frontend display (double converted):", frontendDisplay + " (Dili Time)");
    
    return frontendDisplay;
}

// Run the simulation
const backendTimestamp = simulateBackendConversion();
const frontendDisplay = simulateFrontendConversion(backendTimestamp);

console.log("\n" + "=".repeat(60));
console.log("ANALYSIS:");
console.log("=".repeat(60));
console.log("• Database time: 07:50 UTC");
console.log("• Expected Dili time: 16:50 (UTC+9)");
console.log("• Actual displayed time: " + frontendDisplay);
console.log("• Issue: Double conversion (UTC+9 in backend, then +9 again in frontend)");

console.log("\n" + "=".repeat(60));
console.log("SOLUTION OPTIONS:");
console.log("=".repeat(60));
console.log("Option 1: Remove backend conversion, let frontend handle all timezone conversion");
console.log("Option 2: Backend returns UTC, add timezone info to indicate conversion needed");
console.log("Option 3: Backend includes timezone info in the response format");
