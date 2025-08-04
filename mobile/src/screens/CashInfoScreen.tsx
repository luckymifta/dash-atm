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
  Dimensions,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import atmService from '../services/atmService';
import { CashInfo } from '../types/index';

const { width } = Dimensions.get('window');

const CashInfoScreen: React.FC = () => {
  const [cashData, setCashData] = useState<CashInfo[]>([]);
  const [filteredCashData, setFilteredCashData] = useState<CashInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sortBy, setSortBy] = useState<'terminal_id' | 'total_cash' | 'days_remaining'>('terminal_id');

  useEffect(() => {
    fetchCashData();
  }, []);

  useEffect(() => {
    filterAndSortData();
  }, [cashData, searchQuery, sortBy]);

  const fetchCashData = async () => {
    try {
      // Since we don't have a bulk cash endpoint, we'll need to fetch regional data first
      // and then get cash info for each terminal
      const regionData = await atmService.getRegionalData();
      const allTerminals: any[] = [];
      
      regionData.forEach((region: any) => {
        allTerminals.push(...region.terminals);
      });
      
      // For demo purposes, we'll create mock cash data
      // In a real app, you'd call atmService.getCashInfo for each terminal
      const mockCashData: CashInfo[] = allTerminals.map((terminal: any) => ({
        terminal_id: terminal.terminal_id,
        denomination_20k: Math.floor(Math.random() * 500) + 100,
        denomination_50k: Math.floor(Math.random() * 300) + 50,
        denomination_100k: Math.floor(Math.random() * 200) + 20,
        total_cash: 0, // Will be calculated
        last_refill: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
        estimated_days_remaining: Math.floor(Math.random() * 30) + 1,
      }));

      // Calculate total cash
      mockCashData.forEach(item => {
        item.total_cash = (item.denomination_20k * 20000) + 
                         (item.denomination_50k * 50000) + 
                         (item.denomination_100k * 100000);
      });

      setCashData(mockCashData);
    } catch (error) {
      console.error('Cash data fetch error:', error);
      Alert.alert('Error', 'Failed to load cash information');
    } finally {
      setIsLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchCashData();
    setRefreshing(false);
  };

  const filterAndSortData = () => {
    let filtered = cashData;

    // Filter by search query
    if (searchQuery.trim()) {
      filtered = filtered.filter((item: CashInfo) =>
        item.terminal_id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Sort data
    filtered.sort((a: CashInfo, b: CashInfo) => {
      switch (sortBy) {
        case 'terminal_id':
          return a.terminal_id.localeCompare(b.terminal_id);
        case 'total_cash':
          return b.total_cash - a.total_cash;
        case 'days_remaining':
          return a.estimated_days_remaining - b.estimated_days_remaining;
        default:
          return 0;
      }
    });

    setFilteredCashData(filtered);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const getDaysRemainingColor = (days: number) => {
    if (days <= 3) return '#F44336';
    if (days <= 7) return '#FF9800';
    return '#4CAF50';
  };

  const sortOptions = [
    { key: 'terminal_id', label: 'Terminal ID' },
    { key: 'total_cash', label: 'Total Cash' },
    { key: 'days_remaining', label: 'Days Remaining' },
  ];

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <Ionicons name="sync" size={50} color="#1976D2" />
        <Text style={styles.loadingText}>Loading cash information...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Cash Information</Text>
        <Text style={styles.headerSubtitle}>
          {filteredCashData.length} terminals
        </Text>
      </View>

      <View style={styles.controlsContainer}>
        <View style={styles.searchBox}>
          <View style={styles.searchIcon}>
            <Ionicons name="search" size={20} color="#666" />
          </View>
          <TextInput
            style={styles.searchInput}
            placeholder="Search by terminal ID"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>

        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false} 
          style={styles.sortContainer}
        >
          <Text style={styles.sortLabel}>Sort by:</Text>
          {sortOptions.map((option) => (
            <TouchableOpacity
              key={option.key}
              style={[
                styles.sortButton,
                sortBy === option.key && styles.sortButtonActive
              ]}
              onPress={() => setSortBy(option.key as any)}
            >
              <Text
                style={[
                  styles.sortButtonText,
                  sortBy === option.key && styles.sortButtonTextActive
                ]}
              >
                {option.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      <ScrollView
        style={styles.cashList}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {filteredCashData.map((cashInfo: CashInfo, index: number) => (
          <View key={index} style={styles.cashCard}>
            <View style={styles.cashHeader}>
              <View style={styles.terminalInfo}>
                <Text style={styles.terminalId}>{cashInfo.terminal_id}</Text>
                <Text style={styles.totalCash}>
                  {formatCurrency(cashInfo.total_cash)}
                </Text>
              </View>
              
              <View style={styles.daysContainer}>
                <View style={[
                  styles.daysIndicator,
                  { backgroundColor: getDaysRemainingColor(cashInfo.estimated_days_remaining) }
                ]}>
                  <Text style={styles.daysNumber}>
                    {cashInfo.estimated_days_remaining}
                  </Text>
                </View>
                <Text style={styles.daysLabel}>Days Left</Text>
              </View>
            </View>

            <View style={styles.denominationGrid}>
              <View style={styles.denominationCard}>
                <View style={[styles.denominationHeader, { backgroundColor: '#E8F5E8' }]}>
                  <Ionicons name="card" size={20} color="#4CAF50" />
                  <Text style={styles.denominationTitle}>20K</Text>
                </View>
                <Text style={styles.denominationCount}>
                  {cashInfo.denomination_20k.toLocaleString()} pcs
                </Text>
                <Text style={styles.denominationValue}>
                  {formatCurrency(cashInfo.denomination_20k * 20000)}
                </Text>
              </View>

              <View style={styles.denominationCard}>
                <View style={[styles.denominationHeader, { backgroundColor: '#FFF3E0' }]}>
                  <Ionicons name="card" size={20} color="#FF9800" />
                  <Text style={styles.denominationTitle}>50K</Text>
                </View>
                <Text style={styles.denominationCount}>
                  {cashInfo.denomination_50k.toLocaleString()} pcs
                </Text>
                <Text style={styles.denominationValue}>
                  {formatCurrency(cashInfo.denomination_50k * 50000)}
                </Text>
              </View>

              <View style={styles.denominationCard}>
                <View style={[styles.denominationHeader, { backgroundColor: '#E3F2FD' }]}>
                  <Ionicons name="card" size={20} color="#1976D2" />
                  <Text style={styles.denominationTitle}>100K</Text>
                </View>
                <Text style={styles.denominationCount}>
                  {cashInfo.denomination_100k.toLocaleString()} pcs
                </Text>
                <Text style={styles.denominationValue}>
                  {formatCurrency(cashInfo.denomination_100k * 100000)}
                </Text>
              </View>
            </View>

            <View style={styles.refillInfo}>
              <Ionicons name="time-outline" size={16} color="#666" />
              <Text style={styles.refillText}>
                Last refill: {new Date(cashInfo.last_refill).toLocaleDateString()}
              </Text>
            </View>
          </View>
        ))}

        {filteredCashData.length === 0 && (
          <View style={styles.emptyContainer}>
            <Ionicons name="card-outline" size={50} color="#ccc" />
            <Text style={styles.emptyText}>No cash data found</Text>
            <Text style={styles.emptySubtext}>
              Try adjusting your search criteria
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
  controlsContainer: {
    backgroundColor: 'white',
    padding: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  searchBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    paddingHorizontal: 15,
    marginBottom: 15,
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
  sortContainer: {
    flexDirection: 'row',
  },
  sortLabel: {
    fontSize: 14,
    color: '#666',
    marginRight: 15,
    alignSelf: 'center',
  },
  sortButton: {
    paddingHorizontal: 15,
    paddingVertical: 6,
    marginRight: 10,
    borderRadius: 15,
    backgroundColor: '#f5f5f5',
  },
  sortButtonActive: {
    backgroundColor: '#1976D2',
  },
  sortButtonText: {
    fontSize: 12,
    color: '#666',
  },
  sortButtonTextActive: {
    color: 'white',
  },
  cashList: {
    flex: 1,
    padding: 15,
  },
  cashCard: {
    backgroundColor: 'white',
    borderRadius: 15,
    padding: 20,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  cashHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
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
  totalCash: {
    fontSize: 16,
    color: '#1976D2',
    fontWeight: '600',
  },
  daysContainer: {
    alignItems: 'center',
  },
  daysIndicator: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 5,
  },
  daysNumber: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  daysLabel: {
    fontSize: 12,
    color: '#666',
  },
  denominationGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15,
  },
  denominationCard: {
    flex: 1,
    marginHorizontal: 5,
    padding: 15,
    backgroundColor: '#fafafa',
    borderRadius: 10,
    alignItems: 'center',
  },
  denominationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 15,
    marginBottom: 10,
  },
  denominationTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginLeft: 5,
  },
  denominationCount: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  denominationValue: {
    fontSize: 12,
    color: '#333',
    fontWeight: '600',
  },
  refillInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
  },
  refillText: {
    fontSize: 14,
    color: '#666',
    marginLeft: 8,
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

export default CashInfoScreen;
