import {defineConfig} from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'http://localhost:8000/openapi.json', // sign up at app.heyapi.dev
  output: 'src/api',
  plugins: ['@hey-api/typescript', { name: '@hey-api/client-axios', runtimeConfigPath: '@/hey-api' },{
      asClass: true, // default
      name: '@hey-api/sdk',
    },],
});