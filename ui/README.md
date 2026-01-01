# JDK Compliance Scanner - UI

Frontend UI for the JDK Compliance Scanner application.

## Tech Stack

- **React 18+** with TypeScript
- **Vite** - Build tool
- **React Router** - Routing
- **Zustand** - State management
- **Axios** - HTTP client
- **React Hook Form** - Form handling
- **Recharts** - Charts
- **Lucide React** - Icons
- **CSS Modules** - Styling with CSS Variables

## Design Principles

- **DRY** (Don't Repeat Yourself): Reusable components and utilities
- **KISS** (Keep It Simple): Simple, straightforward interfaces
- **MISS** (Minimum Information, Simple Structure): Clean, uncluttered design
- **No Gradients**: Solid colors only, professional appearance
- **Custom Design System**: CSS Variables for consistent theming

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm

### Installation

```bash
cd ui
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
ui/
├── src/
│   ├── components/      # Reusable components
│   │   ├── common/     # Button, Input, Card, Badge, Modal
│   │   ├── layout/     # Layout components
│   │   ├── forms/      # Form components
│   │   └── charts/     # Chart components
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── store/          # State management (Zustand)
│   ├── types/          # TypeScript types
│   ├── hooks/          # Custom hooks
│   ├── utils/          # Utility functions
│   └── styles/         # Global styles and CSS variables
├── public/             # Static assets
└── package.json
```

## Environment Variables

Create a `.env` file:

```
VITE_API_BASE_URL=http://localhost:8000
```

## API Integration

The UI communicates with the backend API at the configured base URL. All API calls go through the centralized service layer in `src/services/api/`.

## Features

- Clean, professional design without gradients
- Responsive layout
- Authentication with JWT tokens
- Role-based access control
- Reusable component library
- Type-safe API integration

## Status

🚧 Under Development

- [x] Project setup
- [x] Design system (CSS variables)
- [x] Core components (Button, Input, Card, Badge, Modal)
- [x] Authentication (Login page)
- [x] API service layer
- [x] State management
- [ ] Main layout and navigation
- [ ] Dashboard
- [ ] Configuration pages
- [ ] Scanner pages
- [ ] Reports
- [ ] Exemptions
