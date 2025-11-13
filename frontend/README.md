# Home Temperature Monitor - Frontend

A React + Vite + Tailwind CSS frontend application for monitoring home temperature readings.

## Features

- 🔐 Authentication (Login/Signup) with automatic token refresh
- 📊 Interactive temperature graph with date filtering
- 🎨 Modern UI built with Tailwind CSS
- 🔄 Automatic token refresh on API calls
- 🛡️ Protected routes requiring authentication

## Tech Stack

- **React** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **Recharts** - Chart library
- **Axios** - HTTP client
- **date-fns** - Date utilities

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

3. Update `.env` with your backend API URL:
```
VITE_API_BASE_URL=http://localhost:5000
```

### Development

Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173` (or the port Vite assigns).

### Build

Build for production:
```bash
npm run build
```

### Preview

Preview the production build:
```bash
npm run preview
```

## Project Structure

```
src/
├── components/       # Reusable components
│   └── ProtectedRoute.tsx
├── contexts/        # React contexts
│   └── AuthContext.tsx
├── pages/          # Page components
│   ├── Login.tsx
│   ├── Signup.tsx
│   └── Dashboard.tsx
├── services/       # API services
│   ├── api.ts      # Axios instance with token refresh
│   ├── authService.ts
│   └── readingsService.ts
├── types/          # TypeScript types
│   └── index.ts
├── App.tsx         # Main app component
├── main.tsx        # Entry point
├── index.css       # Global styles
└── config.ts       # Configuration
```

## Authentication Flow

1. User logs in or signs up
2. Access token and refresh token are stored in localStorage
3. Access token is automatically added to API requests
4. On 401 errors, the refresh token is used to get a new access token
5. If refresh fails, user is redirected to login

## API Integration

The frontend expects the backend API to be running on `http://localhost:5000` (or the URL specified in `.env`).

### Endpoints Used

- `POST /api/login` - User login
- `POST /api/signup` - User registration
- `POST /api/refresh-token` - Token refresh
- `POST /api/logout` - User logout
- `GET /api/readings` - Get temperature readings (with optional `startDateTime` and `endDateTime` query params)

## License

MIT

