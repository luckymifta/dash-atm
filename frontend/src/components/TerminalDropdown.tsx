'use client';

import React, { useState, useEffect } from 'react';
import { ChevronDown, Monitor, MapPin, AlertCircle } from 'lucide-react';
import { atmApiService, ATMListItem } from '@/services/atmApi';

interface TerminalDropdownProps {
  value: string;
  onChange: (terminalId: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  error?: string;
}

export function TerminalDropdown({
  value,
  onChange,
  placeholder = 'Select Terminal ID',
  disabled = false,
  className = '',
  error
}: TerminalDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [terminals, setTerminals] = useState<ATMListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  // Fetch terminal list on component mount
  useEffect(() => {
    const fetchTerminals = async () => {
      try {
        setLoading(true);
        setLoadError(null);
        const response = await atmApiService.getATMList(undefined, undefined, 1000);
        setTerminals(response.atms);
      } catch (err) {
        console.error('Failed to fetch terminal list:', err);
        setLoadError('Failed to load terminals');
      } finally {
        setLoading(false);
      }
    };

    fetchTerminals();
  }, []);

  const selectedTerminal = terminals.find(terminal => terminal.terminal_id === value);

  const handleSelect = (terminalId: string) => {
    onChange(terminalId);
    setIsOpen(false);
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return 'bg-green-100 text-green-800';
      case 'WARNING':
        return 'bg-yellow-100 text-yellow-800';
      case 'WOUNDED':
        return 'bg-orange-100 text-orange-800';
      case 'ZOMBIE':
        return 'bg-purple-100 text-purple-800';
      case 'OUT_OF_SERVICE':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className={`relative ${className}`}>
        <div className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md bg-gray-50">
          <Monitor className="h-4 w-4 text-gray-400" />
          <span className="text-gray-500">Loading terminals...</span>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={`relative ${className}`}>
        <div className="flex items-center space-x-2 px-3 py-2 border border-red-300 rounded-md bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <span className="text-red-700">{loadError}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full flex items-center justify-between px-3 py-2 border rounded-md text-left focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
          disabled 
            ? 'bg-gray-50 text-gray-500 cursor-not-allowed border-gray-200' 
            : error
            ? 'border-red-300 bg-red-50 hover:border-red-400'
            : 'border-gray-300 bg-white hover:border-gray-400'
        }`}
      >
        <div className="flex items-center space-x-2 flex-1 min-w-0">
          <Monitor className={`h-4 w-4 flex-shrink-0 ${disabled ? 'text-gray-400' : 'text-gray-600'}`} />
          {selectedTerminal ? (
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-900 truncate">
                {selectedTerminal.terminal_id}
              </div>
              <div className="flex items-center space-x-2 mt-1">
                <MapPin className="h-3 w-3 text-gray-400 flex-shrink-0" />
                <span className="text-xs text-gray-500 truncate">
                  {selectedTerminal.location}
                </span>
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusBadgeColor(selectedTerminal.current_status)}`}>
                  {selectedTerminal.current_status}
                </span>
              </div>
            </div>
          ) : (
            <span className={disabled ? 'text-gray-500' : 'text-gray-700'}>
              {placeholder}
            </span>
          )}
        </div>
        <ChevronDown className={`h-4 w-4 flex-shrink-0 transition-transform ${
          isOpen ? 'transform rotate-180' : ''
        } ${disabled ? 'text-gray-400' : 'text-gray-600'}`} />
      </button>

      {isOpen && !disabled && (
        <>
          {/* Overlay to close dropdown when clicking outside */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Dropdown menu */}
          <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
            {terminals.length === 0 ? (
              <div className="px-4 py-3 text-sm text-gray-500 text-center">
                No terminals available
              </div>
            ) : (
              <>
                {/* Search/filter could be added here in the future */}
                {terminals.map((terminal) => (
                  <button
                    key={terminal.terminal_id}
                    type="button"
                    onClick={() => handleSelect(terminal.terminal_id)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition-colors ${
                      value === terminal.terminal_id 
                        ? 'bg-blue-50 border-l-4 border-blue-500' 
                        : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className={`font-medium truncate ${
                          value === terminal.terminal_id ? 'text-blue-900' : 'text-gray-900'
                        }`}>
                          {terminal.terminal_id}
                        </div>
                        <div className="flex items-center space-x-1 mt-1">
                          <MapPin className="h-3 w-3 text-gray-400 flex-shrink-0" />
                          <span className="text-xs text-gray-600 truncate">
                            {terminal.location}
                          </span>
                        </div>
                        <div className="mt-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getStatusBadgeColor(terminal.current_status)}`}>
                            {terminal.current_status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </>
            )}
          </div>
        </>
      )}
      
      {error && (
        <p className="mt-1 text-sm text-red-600 flex items-center">
          <AlertCircle className="h-4 w-4 mr-1" />
          {error}
        </p>
      )}
    </div>
  );
}
