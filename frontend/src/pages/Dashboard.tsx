import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { readingsService } from '../services/readingsService';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { Reading } from '../types';
import { format, parseISO } from 'date-fns';
import { localToUTC, formatForDateTimeLocal } from '../utils/dateUtils';

// Default date range: 2025-11-04 00:00:00 to 01:00:00 (local time)
const getDefaultStartDateTime = (): string => {
  const date = new Date(2025, 10, 4, 0, 0, 0); // Month is 0-indexed, so 10 = November
  return formatForDateTimeLocal(date);
};

const getDefaultEndDateTime = (): string => {
  const date = new Date(2025, 10, 4, 1, 0, 0); // Month is 0-indexed, so 10 = November
  return formatForDateTimeLocal(date);
};

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const [readings, setReadings] = useState<Reading[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [startDateTime, setStartDateTime] = useState(getDefaultStartDateTime());
  const [endDateTime, setEndDateTime] = useState(getDefaultEndDateTime());

  const fetchReadings = async () => {
    if (!startDateTime || !endDateTime) {
      setError('Both start and end date/time are required');
      return;
    }

    setIsLoading(true);
    setError('');
    try {
      // Convert local time to UTC before sending
      const startUTC = localToUTC(startDateTime);
      const endUTC = localToUTC(endDateTime);
      
      const data = await readingsService.getReadings(startUTC, endUTC);
      // Sort by recordedAt
      data.sort((a, b) => 
        new Date(a.recordedAt).getTime() - new Date(b.recordedAt).getTime()
      );
      setReadings(data);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { error?: string; message?: string } } };
        const errorMessage = axiosError.response?.data?.error || axiosError.response?.data?.message || 'Failed to fetch readings';
        setError(errorMessage);
      } else if (err instanceof Error) {
        setError(err.message || 'Failed to fetch readings');
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReadings();
  }, []);

  const handleApplyFilter = () => {
    fetchReadings();
  };

  const handleClearFilter = () => {
    setStartDateTime(getDefaultStartDateTime());
    setEndDateTime(getDefaultEndDateTime());
    // Fetch with default range after clearing
    setTimeout(() => {
      fetchReadings();
    }, 0);
  };

  // Format data for chart
  const chartData = readings.map((reading) => ({
    dateTime: format(parseISO(reading.recordedAt), 'MMM dd, yyyy HH:mm'),
    temperature: reading.tempC,
    timestamp: reading.recordedAt,
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Home Temperature Monitor</h1>
              <p className="text-sm text-gray-600">Welcome, {user?.username}</p>
            </div>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filter Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Filter by Date Range</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="startDateTime" className="block text-sm font-medium text-gray-700 mb-1">
                Start Date & Time
              </label>
              <input
                id="startDateTime"
                type="datetime-local"
                value={startDateTime}
                onChange={(e) => setStartDateTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label htmlFor="endDateTime" className="block text-sm font-medium text-gray-700 mb-1">
                End Date & Time
              </label>
              <input
                id="endDateTime"
                type="datetime-local"
                value={endDateTime}
                onChange={(e) => setEndDateTime(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="flex items-end gap-2">
              <button
                onClick={handleApplyFilter}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Apply
              </button>
              <button
                onClick={handleClearFilter}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}

        {/* Chart Section */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Temperature Readings</h2>
          {isLoading ? (
            <div className="flex items-center justify-center h-96">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : readings.length === 0 ? (
            <div className="flex items-center justify-center h-96 text-gray-500">
              <p>No readings available for the selected date range.</p>
            </div>
          ) : (
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="dateTime" 
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    interval="preserveStartEnd"
                  />
                  <YAxis 
                    label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip 
                    formatter={(value: number) => [`${value.toFixed(2)} °C`, 'Temperature']}
                    labelFormatter={(label) => `Time: ${label}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="temperature" 
                    stroke="#2563eb" 
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    name="Temperature (°C)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          {!isLoading && readings.length > 0 && (
            <div className="mt-4 text-sm text-gray-600">
              Showing {readings.length} reading{readings.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

