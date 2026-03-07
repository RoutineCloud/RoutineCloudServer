# Routine Cloud Frontend

This is the frontend for the Routine Cloud application, built with Vue 3, Vite, Pinia, and Vuetify.

## Setup

### Prerequisites

- Node.js (v16 or later)
- npm or yarn

### Installation

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   # or
   yarn install
   ```

### Development

1. Start the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

2. Open your browser and navigate to http://localhost:3000

### Building for Production

1. Build the application:
   ```bash
   npm run build
   # or
   yarn build
   ```

2. Preview the production build:
   ```bash
   npm run preview
   # or
   yarn preview
   ```

## Project Structure

- `src/` - Source code
  - `assets/` - Static assets (images, fonts, etc.)
  - `components/` - Reusable Vue components
  - `router/` - Vue Router configuration
  - `stores/` - Pinia stores for state management
  - `views/` - Page components
  - `App.vue` - Root component
  - `main.js` - Application entry point

## Features

- **Authentication** - OIDC-based authentication (Zitadel by default)
- **Alexa Integration** - OAuth authorization for Alexa account linking
- **Responsive Design** - Works on desktop and mobile devices
- **State Management** - Using Pinia for a better developer experience

## Available Pages

- **Home** - Landing page
- **About** - Information about the application
- **Login** - User authentication
- **OAuth Authorize** - For Alexa account linking

## Adding New Pages

1. Create a new Vue component in the `src/views` directory
2. Add a route in `src/router/index.js`
3. Link to the new page from the navigation menu or other pages

## State Management

The application uses Pinia for state management. There are two main stores:

- **User Store** - Handles authentication and user data
- **Routines Store** - Manages user routines

To use a store in a component:

```javascript
import { useUserStore, useRoutinesStore } from '@/stores';

// In setup()
const userStore = useUserStore();
const routinesStore = useRoutinesStore();

// Access state
console.log(userStore.isAuthenticated);
console.log(routinesStore.allRoutines);

// Call actions
userStore.login(email, password);
routinesStore.fetchRoutines();
```