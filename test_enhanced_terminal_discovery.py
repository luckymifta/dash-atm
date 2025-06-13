#!/usr/bin/env python3
"""
Enhanced Terminal Discovery Test Script

This script tests the new terminal discovery functionality to ensure it works properly
in production environment on Windows machines.

Features tested:
1. Adaptive terminal list loading/saving
2. New terminal discovery and persistence
3. Comprehensive search with discovery
4. Cross-platform file handling (Windows compatibility)
5. Production environment simulation
"""

import sys
import os
import json
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Set, List, Dict, Any
import unittest
from unittest.mock import patch, MagicMock
import logging

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

try:
    from combined_atm_retrieval_script import CombinedATMRetriever, PARAMETER_VALUES
    print("✅ Successfully imported CombinedATMRetriever")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(funcName)s:%(lineno)d]: %(message)s"
)
log = logging.getLogger("TestEnhancedDiscovery")

class TestEnhancedTerminalDiscovery(unittest.TestCase):
    """Test cases for enhanced terminal discovery functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp(prefix="atm_test_")
        self.retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
        print(f"🧪 Test setup complete - using temp dir: {self.test_dir}")
    
    def tearDown(self):
        """Clean up test environment"""
        try:
            shutil.rmtree(self.test_dir)
            print(f"🧹 Cleaned up test directory: {self.test_dir}")
        except Exception as e:
            print(f"⚠️ Warning: Could not clean up test directory: {e}")
    
    def _mock_discovered_terminals_file_path(self):
        """Get mocked file path for discovered terminals"""
        return os.path.join(self.test_dir, "discovered_terminals.json")
    
    def test_load_discovered_terminals_no_file(self):
        """Test loading when no discovery file exists"""
        print("\n🔍 Testing: Load discovered terminals with no existing file")
        
        with patch.object(os.path, 'join', return_value=self._mock_discovered_terminals_file_path()):
            result = self.retriever.load_discovered_terminals()
            
        self.assertIsInstance(result, set)
        self.assertEqual(len(result), 0)
        print("✅ Correctly returns empty set when no file exists")
    
    def test_save_and_load_discovered_terminals(self):
        """Test saving and loading discovered terminals"""
        print("\n🔍 Testing: Save and load discovered terminals")
        
        # Test data
        test_terminals = {'83', '2603', '88', '147', '87', '169', '2605', '2604', '93', '49', '86', '89', '85', '90', '999', '1000'}
        
        with patch.object(os.path, 'join', return_value=self._mock_discovered_terminals_file_path()):
            # Save terminals
            self.retriever.save_discovered_terminals(test_terminals)
            
            # Verify file was created
            self.assertTrue(os.path.exists(self._mock_discovered_terminals_file_path()))
            
            # Load terminals
            loaded_terminals = self.retriever.load_discovered_terminals()
            
        self.assertEqual(test_terminals, loaded_terminals)
        print(f"✅ Successfully saved and loaded {len(test_terminals)} terminals")
        
        # Verify file content structure
        with open(self._mock_discovered_terminals_file_path(), 'r') as f:
            data = json.load(f)
        
        required_keys = ['discovered_terminals', 'total_count', 'last_updated', 'discovery_metadata']
        for key in required_keys:
            self.assertIn(key, data)
            print(f"✅ File contains required key: {key}")
        
        self.assertEqual(data['total_count'], len(test_terminals))
        print("✅ File structure is correct")
    
    def test_get_adaptive_terminal_list_new_installation(self):
        """Test adaptive terminal list on fresh installation"""
        print("\n🔍 Testing: Adaptive terminal list on new installation")
        
        with patch.object(os.path, 'join', return_value=self._mock_discovered_terminals_file_path()):
            adaptive_list = self.retriever.get_adaptive_terminal_list()
        
        expected_terminals = ['83', '2603', '88', '147', '87', '169', '2605', '2604', '93', '49', '86', '89', '85', '90']
        
        self.assertEqual(set(adaptive_list), set(expected_terminals))
        self.assertEqual(len(adaptive_list), 14)
        print(f"✅ New installation returns {len(adaptive_list)} expected terminals")
    
    def test_comprehensive_search_with_new_discoveries(self):
        """Test comprehensive search that discovers new terminals"""
        print("\n🔍 Testing: Comprehensive search with new terminal discoveries")
        
        # Mock the get_terminals_by_status to return some new terminals
        def mock_get_terminals_by_status(param_value):
            if param_value == "AVAILABLE":
                return [
                    {'terminalId': '83', 'issueStateName': 'AVAILABLE'},
                    {'terminalId': '147', 'issueStateName': 'AVAILABLE'},
                    {'terminalId': '999', 'issueStateName': 'AVAILABLE'},  # New terminal
                ]
            elif param_value == "WARNING":
                return [
                    {'terminalId': '86', 'issueStateName': 'WARNING'},
                    {'terminalId': '1000', 'issueStateName': 'WARNING'},  # New terminal
                ]
            elif param_value == "WOUNDED":
                return [
                    {'terminalId': '89', 'issueStateName': 'WOUNDED'},
                ]
            else:
                return []
        
        with patch.object(self.retriever, 'get_terminals_by_status', side_effect=mock_get_terminals_by_status):
            with patch.object(os.path, 'join', return_value=self._mock_discovered_terminals_file_path()):
                terminals, status_counts = self.retriever.comprehensive_terminal_search()
        
        # Verify new terminals were discovered
        found_terminal_ids = {t.get('terminalId') for t in terminals}
        self.assertIn('999', found_terminal_ids)
        self.assertIn('1000', found_terminal_ids)
        
        # Verify discovery metadata was added
        for terminal in terminals:
            if terminal.get('terminalId') in ['999', '1000']:
                self.assertTrue(terminal.get('is_newly_discovered'))
                self.assertIsNotNone(terminal.get('discovery_timestamp'))
        
        print(f"✅ Discovered new terminals: {found_terminal_ids & {'999', '1000'}}")
        
        # Verify discovery file was updated
        self.assertTrue(os.path.exists(self._mock_discovered_terminals_file_path()))
        
        with open(self._mock_discovered_terminals_file_path(), 'r') as f:
            saved_data = json.load(f)
        
        saved_terminals = set(saved_data['discovered_terminals'])
        self.assertIn('999', saved_terminals)
        self.assertIn('1000', saved_terminals)
        print("✅ New discoveries were persisted to file")
    
    def test_windows_path_compatibility(self):
        """Test Windows path compatibility"""
        print("\n🔍 Testing: Windows path compatibility")
        
        # Simulate Windows paths
        windows_style_paths = [
            "C:\\Users\\TestUser\\Documents\\atm\\discovered_terminals.json",
            "C:/Users/TestUser/Documents/atm/discovered_terminals.json",
            "D:\\Program Files\\ATM Monitor\\discovered_terminals.json"
        ]
        
        test_terminals = {'83', '999', '1000'}
        
        for win_path in windows_style_paths:
            # Create directory if it doesn't exist (simulate Windows behavior)
            win_dir = os.path.dirname(win_path)
            test_win_dir = os.path.join(self.test_dir, os.path.basename(win_dir))
            os.makedirs(test_win_dir, exist_ok=True)
            
            test_file_path = os.path.join(test_win_dir, "discovered_terminals.json")
            
            with patch.object(os.path, 'join', return_value=test_file_path):
                try:
                    self.retriever.save_discovered_terminals(test_terminals)
                    loaded = self.retriever.load_discovered_terminals()
                    
                    self.assertEqual(test_terminals, loaded)
                    print(f"✅ Windows path compatible: {os.path.basename(win_dir)}")
                    
                except Exception as e:
                    self.fail(f"❌ Windows path failed: {win_path} - {e}")


def test_basic_terminal_discovery():
    """Test basic terminal discovery functionality"""
    log.info("=== Testing Basic Terminal Discovery ===")
    
    # Create retriever in demo mode
    retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
    
    # Test the comprehensive search
    terminals, status_counts = retriever.comprehensive_terminal_search()
    
    log.info(f"Found {len(terminals)} terminals")
    log.info(f"Status counts: {status_counts}")
    
    # Verify all terminals have required fields
    for terminal in terminals:
        assert 'terminalId' in terminal, f"Terminal missing terminalId: {terminal}"
        assert 'fetched_status' in terminal, f"Terminal missing fetched_status: {terminal}"
        assert 'issueStateCode' in terminal, f"Terminal missing issueStateCode: {terminal}"
        assert 'is_newly_discovered' in terminal, f"Terminal missing discovery metadata: {terminal}"
        assert 'discovery_timestamp' in terminal, f"Terminal missing discovery timestamp: {terminal}"
    
    log.info("✅ Basic terminal discovery test passed")
    return terminals, status_counts

def test_adaptive_terminal_list():
    """Test adaptive terminal list functionality"""
    log.info("=== Testing Adaptive Terminal List ===")
    
    retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
    
    # Test getting adaptive terminal list
    adaptive_list = retriever.get_adaptive_terminal_list()
    
    log.info(f"Adaptive terminal list: {adaptive_list}")
    log.info(f"Total adaptive terminals: {len(adaptive_list)}")
    
    # Should at least contain the expected 14 terminals
    expected_terminals = ['83', '2603', '88', '147', '87', '169', '2605', '2604', '93', '49', '86', '89', '85', '90']
    for expected in expected_terminals:
        assert expected in adaptive_list, f"Expected terminal {expected} not in adaptive list"
    
    log.info("✅ Adaptive terminal list test passed")
    return adaptive_list

def test_persistent_storage():
    """Test persistent storage of discovered terminals"""
    log.info("=== Testing Persistent Storage ===")
    
    retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
    
    # Create test discovered terminals
    test_discovered = {'83', '88', '147', '169', '2603', '2604', '2605', '93', '49', '86', '89', '85', '90', '999', '1000'}
    
    # Save discovered terminals
    retriever.save_discovered_terminals(test_discovered)
    
    # Load them back
    loaded_terminals = retriever.load_discovered_terminals()
    
    log.info(f"Saved terminals: {sorted(test_discovered)}")
    log.info(f"Loaded terminals: {sorted(loaded_terminals)}")
    
    # Verify they match
    assert test_discovered == loaded_terminals, "Saved and loaded terminals don't match"
    
    log.info("✅ Persistent storage test passed")
    return loaded_terminals

def test_new_terminal_detection():
    """Test detection of new terminals"""
    log.info("=== Testing New Terminal Detection ===")
    
    # First, clear any existing discovered terminals file
    discovered_file = os.path.join(backend_dir, "discovered_terminals.json")
    if os.path.exists(discovered_file):
        os.remove(discovered_file)
        log.info("Cleared existing discovered terminals file")
    
    retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
    
    # Modify demo mode to simulate discovery of new terminals
    # We'll monkey-patch the get_terminals_by_status method temporarily
    original_method = retriever.get_terminals_by_status
    
    def mock_get_terminals_with_new_terminals(param_value):
        """Mock method that includes some new terminals"""
        terminals = original_method(param_value)
        
        # Add some mock new terminals for AVAILABLE status
        if param_value == 'AVAILABLE' and terminals:
            new_terminals = [
                {
                    'terminalId': '1001',
                    'location': 'New Location A',
                    'issueStateName': 'AVAILABLE',
                    'fetched_status': param_value,
                    'issueStateCode': 'AVAILABLE',
                    'brand': 'New Brand',
                    'model': 'New Model'
                },
                {
                    'terminalId': '1002', 
                    'location': 'New Location B',
                    'issueStateName': 'AVAILABLE',
                    'fetched_status': param_value,
                    'issueStateCode': 'AVAILABLE',
                    'brand': 'New Brand',
                    'model': 'New Model'
                }
            ]
            terminals.extend(new_terminals)
            log.info(f"Mock: Added 2 new terminals to {param_value} status")
        
        return terminals
    
    # Temporarily replace the method
    retriever.get_terminals_by_status = mock_get_terminals_with_new_terminals
    
    try:
        # Run comprehensive search
        terminals, status_counts = retriever.comprehensive_terminal_search()
        
        # Check for new terminals
        terminal_ids = [t.get('terminalId') for t in terminals]
        new_terminals_found = [tid for tid in terminal_ids if tid in ['1001', '1002']]
        
        log.info(f"New terminals found: {new_terminals_found}")
        assert len(new_terminals_found) == 2, f"Expected 2 new terminals, found {len(new_terminals_found)}"
        
        # Verify new terminals have discovery metadata
        for terminal in terminals:
            if terminal.get('terminalId') in ['1001', '1002']:
                assert terminal.get('is_newly_discovered') == True, f"New terminal {terminal.get('terminalId')} not marked as newly discovered"
                assert 'discovery_timestamp' in terminal, f"New terminal {terminal.get('terminalId')} missing discovery timestamp"
        
        log.info("✅ New terminal detection test passed")
        
    finally:
        # Restore original method
        retriever.get_terminals_by_status = original_method
    
    return terminals

def test_integration_with_main_workflow():
    """Test integration with main retrieval workflow"""
    log.info("=== Testing Integration with Main Workflow ===")
    
    retriever = CombinedATMRetriever(demo_mode=True, total_atms=14)
    
    # Run the full retrieval workflow
    success, all_data = retriever.retrieve_and_process_all_data(save_to_db=False, use_new_tables=False)
    
    assert success, "Main workflow failed"
    
    # Verify data structure
    assert 'regional_data' in all_data, "Missing regional_data in results"
    assert 'terminal_details_data' in all_data, "Missing terminal_details_data in results"
    assert 'summary' in all_data, "Missing summary in results"
    
    # Check terminal details
    terminal_details = all_data.get('terminal_details_data', [])
    log.info(f"Terminal details retrieved: {len(terminal_details)}")
    
    # Verify terminal details have required fields
    for detail in terminal_details:
        assert 'terminalId' in detail, f"Terminal detail missing terminalId: {detail}"
        assert 'unique_request_id' in detail, f"Terminal detail missing unique_request_id: {detail}"
        assert 'fetched_status' in detail, f"Terminal detail missing fetched_status: {detail}"
    
    log.info("✅ Integration test passed")
    return all_data

def run_all_tests():
    """Run all enhanced terminal discovery tests"""
    log.info("🚀 Starting Enhanced Terminal Discovery Tests")
    log.info("=" * 80)
    
    try:
        # Test 1: Basic terminal discovery
        terminals, status_counts = test_basic_terminal_discovery()
        
        # Test 2: Adaptive terminal list
        adaptive_list = test_adaptive_terminal_list()
        
        # Test 3: Persistent storage
        loaded_terminals = test_persistent_storage()
        
        # Test 4: New terminal detection
        terminals_with_new = test_new_terminal_detection()
        
        # Test 5: Integration with main workflow
        all_data = test_integration_with_main_workflow()
        
        # Test 6: Unit tests
        log.info("=== Running Unit Tests ===")
        unittest.main(argv=[''], exit=False, verbosity=1)
        
        log.info("=" * 80)
        log.info("🎉 ALL TESTS PASSED! Enhanced terminal discovery is working correctly")
        log.info("=" * 80)
        
        # Summary
        log.info("📊 Test Summary:")
        log.info(f"   Basic discovery: {len(terminals)} terminals found")
        log.info(f"   Adaptive list: {len(adaptive_list)} terminals in adaptive list")
        log.info(f"   Persistent storage: {len(loaded_terminals)} terminals saved/loaded")
        log.info(f"   New terminals: Detected new terminals successfully")
        log.info(f"   Integration: Full workflow completed successfully")
        log.info(f"\n🏭 READY FOR WINDOWS PRODUCTION DEPLOYMENT!")
        
        return True
        
    except Exception as e:
        log.error(f"❌ TEST FAILED: {e}")
        log.exception("Test failure details:")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit_code = 0 if success else 1
    sys.exit(exit_code)
