import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  TextInput,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import atmService from '../services/atmService';
import { ATMStatus } from '../types/index';

const TerminalDetailsScreen: React.FC = () => {
  const [terminals, setTerminals] = useState<ATMStatus[]>([]);
  const [filteredTerminals, setFilteredTerminals] = useState<ATMStatus[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');

  useEffect(() => {
    fetchTerminals();
  }, []);

  useEffect(() => {
    filterTerminals();
  }, [terminals, searchQuery, selectedFilter]);

  const fetchTerminals = async () => {
    try {
      console.log('Fetching terminal data from status/latest endpoint...');
      const terminals = await atmService.getTerminalStatusList();
      console.log('Terminal data received:', terminals.length, 'terminals');
      console.log('Sample terminal:', terminals[0]);
      
      setTerminals(terminals);
    } catch (error) {
      console.error('Terminal fetch error:', error);
      Alert.alert('Error', 'Failed to load terminal data');
    } finally {
      setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchTerminals();
    setRefreshing(false);
  };

  const filterTerminals = () => {
    let filtered = terminals;

    // Filter by status
    if (selectedFilter !== 'all') {
      filtered = filtered.filter((terminal: any) => terminal.status === selectedFilter);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      filtered = filtered.filter((terminal: any) =>
        terminal.terminal_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        terminal.location.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredTerminals(filtered);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return '#4CAF50';
      case 'offline': return '#F44336';
      case 'maintenance': return '#FF9800';
      case 'out_of_service': return '#9E9E9E';
      default: return '#666';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return 'checkmark-circle';
      case 'offline': return 'close-circle';
      case 'maintenance': return 'construct';
      case 'out_of_service': return 'pause-circle';
      default: return 'help-circle';
    }
  };

  const filterOptions = [
    { key: 'all', label: 'All' },
    { key: 'online', label: 'Online' },
    { key: 'offline', label: 'Offline' },
    { key: 'maintenance', label: 'Maintenance' },
    { key: 'out_of_service', label: 'Out of Service' },
  ];

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="sync" size={50} color="#1976D2" />
        <Text style={styles.loadingText}>Loading terminals...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Terminal Details</Text>
        <Text style={styles.headerSubtitle}>
          {filteredTerminals.length} of {terminals.length} terminals
        </Text>
      </View>

      <View style={styles.searchContainer}>
        <View style={styles.searchBox}>
          <View style={styles.searchIcon}>
            <Ionicons name="search" size={20} color="#666" />
          </View>
          <TextInput
            style={styles.searchInput}
            placeholder="Search by ID or location"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>
      </View>

      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false} 
        style={styles.filterContainer}
      >
        {filterOptions.map((option) => (
          <TouchableOpacity
            key={option.key}
            style={[
              styles.filterButton,
              selectedFilter === option.key && styles.filterButtonActive
            ]}
            onPress={() => setSelectedFilter(option.key)}
          >
            <Text
              style={[
                styles.filterButtonText,
                selectedFilter === option.key && styles.filterButtonTextActive
              ]}
            >
              {option.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView
        style={styles.terminalList}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {filteredTerminals.map((terminal: any, index: number) => (
          <View key={index} style={styles.terminalCard}>
            <View style={styles.terminalHeader}>
              <View style={styles.terminalInfo}>
                <Text style={styles.terminalId}>{terminal.terminal_id}</Text>
                <Text style={styles.terminalLocation}>{terminal.location}</Text>
              </View>
              <View style={styles.statusContainer}>
                <Ionicons
                  name={getStatusIcon(terminal.status) as any}
                  size={24}
                  color={getStatusColor(terminal.status)}
                />
                <Text style={[styles.statusText, { color: getStatusColor(terminal.status) }]}>
                  {terminal.status.replace('_', ' ').toUpperCase()}
                </Text>
              </View>
            </View>
            
            <View style={styles.terminalDetails}>
              <View style={styles.detailRow}>
                <Ionicons name="time-outline" size={16} color="#666" />
                <Text style={styles.detailText}>
                  Last Transaction: {new Date(terminal.last_transaction).toLocaleDateString()}
                </Text>
              </View>
              
              <View style={styles.detailRow}>
                <Ionicons name="card-outline" size={16} color="#666" />
                <Text style={styles.detailText}>
                  Cash Level: {terminal.cash_level}%
                </Text>
              </View>
              
              <View style={styles.detailRow}>
                <Ionicons name="trending-up-outline" size={16} color="#666" />
                <Text style={styles.detailText}>
                  Uptime: {terminal.uptime_percentage.toFixed(1)}%
                </Text>
              </View>
            </View>

            <View style={styles.progressContainer}>
              <Text style={styles.progressLabel}>Cash Level</Text>
              <View style={styles.progressBar}>
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${terminal.cash_level}%`,
                      backgroundColor: terminal.cash_level > 20 ? '#4CAF50' : '#F44336'
                    }
                  ]}
                />
              </View>
            </View>
          </View>
        ))}
        
        {filteredTerminals.length === 0 && (
          <View style={styles.emptyContainer}>
            <Ionicons name="search" size={50} color="#ccc" />
            <Text style={styles.emptyText}>No terminals found</Text>
            <Text style={styles.emptySubtext}>
              Try adjusting your search or filter criteria
            </Text>
          </View>
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
    backgroundColor: 'white',
    padding: 20,
    paddingTop: 50,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  searchContainer: {
    padding: 15,
    backgroundColor: 'white',
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    paddingHorizontal: 15,
  },
  searchIcon: {
    marginRight: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchInput: {
    flex: 1,
    height: 40,
    fontSize: 16,
  },
  filterContainer: {
    backgroundColor: 'white',
    paddingVertical: 10,
    paddingLeft: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  filterButton: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    marginRight: 10,
    borderRadius: 20,
    backgroundColor: '#f5f5f5',
  },
  filterButtonActive: {
    backgroundColor: '#1976D2',
  },
  filterButtonText: {
    fontSize: 14,
    color: '#666',
  },
  filterButtonTextActive: {
    color: 'white',
  },
  terminalList: {
    flex: 1,
    padding: 15,
  },
  terminalCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  terminalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  terminalInfo: {
    flex: 1,
  },
  terminalId: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  terminalLocation: {
    fontSize: 14,
    color: '#666',
  },
  statusContainer: {
    alignItems: 'center',
  },
  statusText: {
    fontSize: 12,
    fontWeight: 'bold',
    marginTop: 5,
  },
  terminalDetails: {
    marginBottom: 15,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  detailText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
  },
  progressContainer: {
    marginTop: 10,
  },
  progressLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  progressBar: {
    height: 6,
    backgroundColor: '#E0E0E0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 50,
  },
  emptyText: {
    fontSize: 18,
    color: '#999',
    marginTop: 15,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#ccc',
    marginTop: 5,
    textAlign: 'center',
  },
});

export default TerminalDetailsScreen;
