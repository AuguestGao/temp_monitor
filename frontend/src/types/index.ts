export interface Reading {
  tempC: number;
  recordedAt: string;
}

export interface ReadingsResponse {
  message: string;
  count: number;
  readings: Reading[];
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface SignupRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  message: string;
  access_token: string;
  refresh_token: string;
}

export interface User {
  username: string;
}

