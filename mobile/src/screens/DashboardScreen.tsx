import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Alert,
  Dimensions,
} from 'react-native';
import { useAuth } from '../contexts/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import atmService from '../services/atmService';
import { DashboardData, ATMSummary } from '../types/index';

const { width } = Dimensions.get('window');

const DashboardScreen: React.FC = () => {
  const { user, logout } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = useCallback(async () => {
    try {
      const data = await atmService.getDashboardData();
      setDashboardData(data);
    } catch (error) {
      console.error('Dashboard fetch error:', error);
      Alert.alert('Error', 'Failed to load dashboard data. Using default values.');
      
      // Set default data to prevent crashes
      setDashboardData({
        summary: {
          total_terminals: 0,
          online: 0,
          offline: 0,
          maintenance: 0,
          out_of_service: 0,
          uptime_percentage: 0
        },
        regional_data: [],
        alerts: [],
        recent_activities: []
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
  }, [fetchDashboardData]);

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Logout', style: 'destructive', onPress: logout },
      ]
    );
  };

  const renderSummaryCard = (title: string, value: number, icon: string, color: string) => (
    <View style={[styles.summaryCard, { borderLeftColor: color }]}>
      <View style={styles.summaryCardContent}>
        <View style={styles.summaryCardText}>
          <Text style={styles.summaryCardTitle}>{title}</Text>
          <Text style={styles.summaryCardValue}>{value}</Text>
        </View>
        <Ionicons name={icon as any} size={30} color={color} />
      </View>
    </View>
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return '#4CAF50';
      case 'offline': return '#F44336';
      case 'maintenance': return '#FF9800';
      case 'out_of_service': return '#9E9E9E';
      default: return '#666';
    }
  };

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="sync" size={50} color="#1976D2" />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.welcomeText}>Welcome back,</Text>
          <Text style={styles.userName}>{user?.username}</Text>
        </View>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
          <Ionicons name="log-out-outline" size={24} color="#666" />
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {dashboardData && dashboardData.summary && (
          <>
            <Text style={styles.sectionTitle}>ATM Status Overview</Text>
            
            <View style={styles.summaryGrid}>
              {renderSummaryCard(
                'Total ATMs', 
                dashboardData.summary.total_terminals || 0, 
                'business-outline', 
                '#1976D2'
              )}
              {renderSummaryCard(
                'Online', 
                dashboardData.summary.online || 0, 
                'checkmark-circle-outline', 
                '#4CAF50'
              )}
              {renderSummaryCard(
                'Offline', 
                dashboardData.summary.offline || 0, 
                'close-circle-outline', 
                '#F44336'
              )}
              {renderSummaryCard(
                'Maintenance', 
                dashboardData.summary.maintenance || 0, 
                'construct-outline', 
                '#FF9800'
              )}
            </View>

            <View style={styles.uptimeCard}>
              <Text style={styles.uptimeTitle}>System Uptime</Text>
              <Text style={styles.uptimeValue}>
                {(dashboardData.summary.uptime_percentage || 0).toFixed(1)}%
              </Text>
              <View style={styles.uptimeBar}>
                <View 
                  style={[
                    styles.uptimeProgress, 
                    { width: `${dashboardData.summary.uptime_percentage || 0}%` }
                  ]} 
                />
              </View>
            </View>

            <Text style={styles.sectionTitle}>Regional Overview</Text>
            
            {dashboardData.regional_data.map((region: any, index: number) => (
              <View key={index} style={styles.regionCard}>
                <View style={styles.regionHeader}>
                  <Text style={styles.regionName}>{region.region}</Text>
                  <Text style={styles.regionCount}>
                    {region.summary.total_terminals} ATMs
                  </Text>
                </View>
                
                <View style={styles.regionStats}>
                  <View style={[styles.statusDot, { backgroundColor: '#4CAF50' }]}>
                    <Text style={styles.statusCount}>{region.summary.online}</Text>
                  </View>
                  <View style={[styles.statusDot, { backgroundColor: '#F44336' }]}>
                    <Text style={styles.statusCount}>{region.summary.offline}</Text>
                  </View>
                  <View style={[styles.statusDot, { backgroundColor: '#FF9800' }]}>
                    <Text style={styles.statusCount}>{region.summary.maintenance}</Text>
                  </View>
                </View>
              </View>
            ))}
          </>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    backgroundColor: 'white',
    paddingTop: 50,
  },
  welcomeText: {
    fontSize: 16,
    color: '#666',
  },
  userName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  logoutButton: {
    padding: 10,
  },
  content: {
    flex: 1,
    padding: 15,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
    marginTop: 10,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  summaryCard: {
    width: (width - 45) / 2,
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  summaryCardContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  summaryCardText: {
    flex: 1,
  },
  summaryCardTitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  summaryCardValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  uptimeCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  uptimeTitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 10,
  },
  uptimeValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1976D2',
    marginBottom: 15,
  },
  uptimeBar: {
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    overflow: 'hidden',
  },
  uptimeProgress: {
    height: '100%',
    backgroundColor: '#1976D2',
  },
  regionCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  regionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  regionName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  regionCount: {
    fontSize: 14,
    color: '#666',
  },
  regionStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statusDot: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statusCount: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
});

export default DashboardScreen;
