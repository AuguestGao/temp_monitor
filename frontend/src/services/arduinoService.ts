import { apiService } from './api';

export interface ArduinoResponse {
  message: string;
  status: 'success' | 'error';
}

class ArduinoService {
  /**
   * Send START command to Arduino
   */
  async start(): Promise<ArduinoResponse> {
    const response = await apiService.getApi().post<ArduinoResponse>('/api/arduino/start');
    return response.data;
  }

  /**
   * Send STOP command to Arduino
   */
  async stop(): Promise<ArduinoResponse> {
    const response = await apiService.getApi().post<ArduinoResponse>('/api/arduino/stop');
    return response.data;
  }

  /**
   * Send TOGGLE command to Arduino
   */
  async toggle(): Promise<ArduinoResponse> {
    const response = await apiService.getApi().post<ArduinoResponse>('/api/arduino/toggle');
    return response.data;
  }
}

export const arduinoService = new ArduinoService();

