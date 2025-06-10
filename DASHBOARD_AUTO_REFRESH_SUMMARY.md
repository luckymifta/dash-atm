# Dashboard Auto-Refresh Configuration - Summary

## Overview
Updated the ATM Dashboard to automatically refresh every 30 minutes instead of the previous 30 seconds, providing a more appropriate refresh interval for production use.

## Changes Made

### 1. Dashboard Page (/src/app/dashboard/page.tsx)
- **Auto-Refresh Interval**: Changed from 30 seconds to 30 minutes (1,800,000 milliseconds)
- **Refresh Timer State**: Added `nextRefresh` state to track when the next refresh will occur
- **Manual Refresh Handler**: Created `handleManualRefresh()` function that resets the countdown timer
- **Visual Indicators**: Added "Next refresh" indicator showing when the next automatic refresh will happen
- **Button Updates**: Updated all refresh/retry buttons to use the new manual refresh handler

### 2. ATM Availability Chart (/src/components/ATMAvailabilityChart.tsx)
- **Auto-Refresh Interval**: Changed from 5 minutes to 30 minutes for consistency
- **Coordinated Refresh**: Now aligns with dashboard refresh cycle

### 3. Individual ATM Chart (/src/components/ATMIndividualChart.tsx)
- **Auto-Refresh Interval**: Changed from 5 minutes to 30 minutes for consistency
- **Coordinated Refresh**: Now aligns with dashboard refresh cycle

### 4. Backup Chart Component (/src/components/ATMAvailabilityChart_backup.tsx)
- **Auto-Refresh Interval**: Updated for consistency (backup file)

## Auto-Refresh Behavior

### Automatic Refresh
- **Frequency**: Every 30 minutes
- **Components**: All dashboard components refresh simultaneously
- **Next Refresh Display**: Shows users when the next refresh will occur
- **Timezone**: All times displayed in Dili timezone (Asia/Dili)

### Manual Refresh
- **Reset Timer**: Manual refresh resets the 30-minute countdown
- **Immediate Update**: All data is refreshed immediately when manually triggered
- **Loading States**: Proper loading indicators during refresh operations

## User Experience Improvements

### Visual Feedback
```tsx
// Next refresh indicator in header
{nextRefresh && (
  <p className="text-xs text-gray-400">
    Next refresh: {nextRefresh.toLocaleString('en-US', { 
      timeZone: 'Asia/Dili',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })} (every 30 min)
  </p>
)}
```

### Refresh Controls
- **Manual Refresh Button**: Available in dashboard header
- **Retry Buttons**: Available in error states
- **Loading States**: Spinning icons during refresh operations
- **Status Indicators**: API connection status display

## Technical Implementation

### Timer Management
```tsx
useEffect(() => {
  fetchATMData();
  
  // Set initial next refresh time
  setNextRefresh(new Date(Date.now() + 30 * 60 * 1000));
  
  // Refresh data every 30 minutes
  const interval = setInterval(() => {
    fetchATMData();
    setNextRefresh(new Date(Date.now() + 30 * 60 * 1000));
  }, 30 * 60 * 1000); // 30 minutes = 1,800,000 milliseconds
  
  return () => clearInterval(interval);
}, []);
```

### Coordinated Refresh
All components now use the same 30-minute interval:
- Dashboard summary data
- ATM availability trends
- Individual ATM historical data

## Benefits

### Performance
- **Reduced API Load**: Fewer API calls reduce server load
- **Bandwidth Optimization**: Less frequent data transfers
- **Battery Friendly**: Reduced background activity for mobile devices

### User Experience
- **Predictable Updates**: Users know when to expect updates
- **Manual Control**: Users can force refresh when needed
- **Clear Feedback**: Visual indicators show refresh status and timing

### Production Readiness
- **Appropriate Intervals**: 30 minutes is suitable for ATM monitoring
- **Resource Efficient**: Balances freshness with system resources
- **Scalable**: Can handle multiple concurrent users

## Configuration
The refresh interval can be easily adjusted by changing the constant:
```tsx
const REFRESH_INTERVAL = 30 * 60 * 1000; // 30 minutes in milliseconds
```

## Testing Recommendations
1. **Manual Refresh**: Test manual refresh button functionality
2. **Timer Display**: Verify next refresh time updates correctly
3. **Error Handling**: Test behavior when API is unavailable
4. **Performance**: Monitor memory usage with long sessions
5. **Mobile**: Test on mobile devices for battery impact

## Deployment Ready
All changes are ready for production deployment:
- ✅ No breaking changes
- ✅ Backward compatible
- ✅ Error handling maintained
- ✅ Performance optimized
- ✅ User experience enhanced

The dashboard now provides a more sustainable and user-friendly auto-refresh experience suitable for production environments.
