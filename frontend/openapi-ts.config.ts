import {defineConfig} from '@hey-api/openapi-ts';

export default defineConfig({
  input: 'http://localhost:8000/v1/openapi.json', // sign up at app.heyapi.dev
  output: 'src/api',
  plugins: [
    '@hey-api/typescript',
    { name: '@hey-api/client-axios', runtimeConfigPath: '../hey-api' },
    {
      name: '@hey-api/sdk',
      asClass: true, // default
      runtimeConfigPath: '../hey-api',
    },
  ],
});