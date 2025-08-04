import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { API_CONFIG } from '../config/api';

const NetworkTestScreen: React.FC = () => {
  const [testResults, setTestResults] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const addTestResult = (message: string) => {
    setTestResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const testNetworkConnectivity = async () => {
    setIsLoading(true);
    setTestResults([]);

    try {
      // Test 1: Basic connectivity
      addTestResult('🔍 Testing basic connectivity...');
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      try {
        const response = await fetch(`${API_CONFIG.USER_API_URL}/auth/login`, {
          method: 'HEAD',
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        addTestResult(`✅ Server is reachable! Status: ${response.status}`);
      } catch (error) {
        clearTimeout(timeoutId);
        if (error instanceof Error) {
          addTestResult(`❌ Connection failed: ${error.message}`);
        }
      }

      // Test 2: Login API test
      addTestResult('🔍 Testing login endpoint...');
      try {
        const loginResponse = await fetch(`${API_CONFIG.USER_API_URL}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: 'admin',
            password: 'admin123'
          }),
        });

        if (loginResponse.ok) {
          addTestResult('✅ Login endpoint is working!');
          const data = await loginResponse.json();
          addTestResult(`✅ Received token: ${data.access_token ? 'YES' : 'NO'}`);
        } else {
          addTestResult(`❌ Login failed with status: ${loginResponse.status}`);
        }
      } catch (error) {
        if (error instanceof Error) {
          addTestResult(`❌ Login test failed: ${error.message}`);
        }
      }

      // Test 3: Main API test
      addTestResult('🔍 Testing main API endpoint...');
      try {
        const mainApiResponse = await fetch(`${API_CONFIG.MAIN_API_URL}/api/v1/health`, {
          method: 'GET',
        });
        addTestResult(`✅ Main API status: ${mainApiResponse.status}`);
      } catch (error) {
        if (error instanceof Error) {
          addTestResult(`❌ Main API test failed: ${error.message}`);
        }
      }

    } catch (error) {
      addTestResult(`❌ Unexpected error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const showConfigInfo = () => {
    Alert.alert(
      'API Configuration',
      `User API: ${API_CONFIG.USER_API_URL}\nMain API: ${API_CONFIG.MAIN_API_URL}`,
      [{ text: 'OK' }]
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Network Connectivity Test</Text>
      
      <View style={styles.buttonContainer}>
        <TouchableOpacity 
          style={[styles.button, isLoading && styles.buttonDisabled]} 
          onPress={testNetworkConnectivity}
          disabled={isLoading}
        >
          <Text style={styles.buttonText}>
            {isLoading ? 'Testing...' : 'Run Network Test'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.infoButton} onPress={showConfigInfo}>
          <Text style={styles.buttonText}>Show Config</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.resultsContainer}>
        {testResults.map((result, index) => (
          <Text key={index} style={styles.resultText}>
            {result}
          </Text>
        ))}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
    color: '#333',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#007AFF',
    padding: 15,
    borderRadius: 8,
    flex: 1,
    marginRight: 10,
  },
  infoButton: {
    backgroundColor: '#34C759',
    padding: 15,
    borderRadius: 8,
    flex: 1,
    marginLeft: 10,
  },
  buttonDisabled: {
    backgroundColor: '#999',
  },
  buttonText: {
    color: 'white',
    textAlign: 'center',
    fontWeight: 'bold',
  },
  resultsContainer: {
    flex: 1,
    backgroundColor: '#000',
    borderRadius: 8,
    padding: 10,
  },
  resultText: {
    color: '#fff',
    fontFamily: 'monospace',
    fontSize: 12,
    marginBottom: 5,
  },
});

export default NetworkTestScreen;
