// Mock API data for testing when the backend database is unavailable
export const mockRegionalData = {
  regional_data: [
    {
      region_code: "TL-DL",
      status_counts: {
        available: 11,
        warning: 1,
        wounded: 2,
        zombie: 0,
        out_of_service: 0,
        total: 14
      },
      availability_percentage: 78.57,
      last_updated: new Date().toISOString(),
      health_status: "HEALTHY" as const
    },
    {
      region_code: "TL-AN", 
      status_counts: {
        available: 12,
        warning: 0,
        wounded: 0,
        zombie: 1,
        out_of_service: 1,
        total: 14
      },
      availability_percentage: 85.71,
      last_updated: new Date().toISOString(),
      health_status: "HEALTHY" as const
    }
  ],
  total_regions: 2,
  summary: {
    available: 23,
    warning: 1,
    wounded: 2,
    zombie: 1,
    out_of_service: 1,
    total: 28
  },
  last_updated: new Date().toISOString()
};

export const generateMockTrends = (regionCode: string, hours: number = 24) => {
  const trends = [];
  const now = new Date();
  
  // Adjust data point interval based on time period
  let intervalHours = 1; // Default 1 hour
  if (hours <= 24) {
    intervalHours = 1; // Every hour for 24h
  } else if (hours <= 168) {
    intervalHours = 6; // Every 6 hours for 7 days
  } else {
    intervalHours = 24; // Every day for 30 days
  }
  
  // Generate data points for the specified time range
  for (let i = hours - intervalHours; i >= 0; i -= intervalHours) {
    const timestamp = new Date(now.getTime() - (i * 60 * 60 * 1000));
    
    // Simulate availability fluctuations based on region and time
    const baseAvailability = regionCode === "TL-DL" ? 78.57 : 85.71;
    const variation = Math.sin(i / 6) * 5 + (Math.random() - 0.5) * 8;
    const availability = Math.max(60, Math.min(95, baseAvailability + variation));
    
    const totalAtms = 14;
    const availableAtms = Math.round((availability / 100) * totalAtms);
    const warningAtms = Math.random() < 0.1 ? 1 : 0;
    const woundedAtms = Math.random() < 0.15 ? Math.floor(Math.random() * 2) + 1 : 0;
    const zombieAtms = Math.random() < 0.05 ? 1 : 0;
    const outOfServiceAtms = totalAtms - availableAtms - warningAtms - woundedAtms - zombieAtms;
    
    trends.push({
      timestamp: timestamp.toISOString(),
      status_counts: {
        available: availableAtms,
        warning: warningAtms,
        wounded: woundedAtms,
        zombie: zombieAtms,
        out_of_service: Math.max(0, outOfServiceAtms),
        total: totalAtms
      },
      availability_percentage: Math.round(availability * 100) / 100
    });
  }
  
  const availabilityValues = trends.map(t => t.availability_percentage);
  
  return {
    region_code: regionCode,
    time_period: `${hours} hours`,
    trends,
    summary_stats: {
      data_points: trends.length,
      time_range_hours: hours,
      avg_availability: Math.round((availabilityValues.reduce((a, b) => a + b, 0) / availabilityValues.length) * 100) / 100,
      min_availability: Math.round(Math.min(...availabilityValues) * 100) / 100,
      max_availability: Math.round(Math.max(...availabilityValues) * 100) / 100,
      first_reading: trends.length > 0 ? trends[0].timestamp : null,
      last_reading: trends.length > 0 ? trends[trends.length - 1].timestamp : null
    }
  };
};
