import { apiService } from './api';
import type { ReadingsResponse, Reading } from '../types';

export const readingsService = {
  async getReadings(startDateTime: string, endDateTime: string): Promise<Reading[]> {
    const params: Record<string, string> = {
      startDateTime,
      endDateTime,
    };

    const response = await apiService
      .getApi()
      .get<ReadingsResponse>('/api/readings', { params });
    return response.data.readings;
  },
};

