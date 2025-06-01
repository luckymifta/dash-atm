// Test the updated Date Created logic with metadata.retrieval_timestamp priority
const testTerminalData = [
  {
    terminal_id: "147",
    retrieved_date: "2025-06-01T09:23:38",
    metadata: JSON.stringify({
      demo_mode: false,
      processing_info: {
        has_location: true,
        has_fault_data: true,
        status_at_retrieval: "WARNING"
      },
      unique_request_id: "1afd8081-0846-4710-bfa2-f4652dd28be2",
      retrieval_timestamp: "2025-06-01T17:46:03.233667+09:00"
    })
  },
  {
    terminal_id: "169",
    retrieved_date: "2025-06-01T08:53:09",
    metadata: JSON.stringify({
      demo_mode: false,
      processing_info: {
        has_location: true,
        has_fault_data: false,
        status_at_retrieval: "WOUNDED"
      },
      unique_request_id: "46d5765b-4119-47c3-ad78-ee5e87c96e49",
      retrieval_timestamp: "2025-06-01T17:15:33.720676+09:00"
    })
  }
];

function formatDateTest(terminal) {
  let dateToFormat = null;
  let dateSource = '';

  // First priority: metadata.retrieval_timestamp (already in Dili time)
  if (terminal.metadata) {
    try {
      const metadata = typeof terminal.metadata === 'string' 
        ? JSON.parse(terminal.metadata) 
        : terminal.metadata;
      if (metadata && typeof metadata === 'object' && 'retrieval_timestamp' in metadata) {
        dateToFormat = metadata.retrieval_timestamp;
        dateSource = 'Retrieved (Dili Time)';
      }
    } catch (error) {
      console.warn('Failed to parse metadata for date:', error);
    }
  }

  // Second priority: retrieved_date
  if (!dateToFormat && terminal.retrieved_date) {
    dateToFormat = terminal.retrieved_date;
    dateSource = 'Retrieved';
  }

  if (!dateToFormat) {
    return 'No date available';
  }

  try {
    const date = new Date(dateToFormat);
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }

    const formattedDate = date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'Asia/Dili'
    });

    const formattedTime = date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Dili'
    });

    return `${formattedDate} ${formattedTime} (${dateSource})`;
  } catch {
    return 'Invalid date format';
  }
}

console.log("Testing Updated Date Created Logic:");
console.log("=".repeat(50));

testTerminalData.forEach((terminal, index) => {
  console.log(`\nTerminal ${terminal.terminal_id}:`);
  console.log(`  Retrieved Date: ${terminal.retrieved_date}`);
  console.log(`  Metadata: ${terminal.metadata}`);
  console.log(`  Formatted: ${formatDateTest(terminal)}`);
});

console.log("\n" + "=".repeat(50));
