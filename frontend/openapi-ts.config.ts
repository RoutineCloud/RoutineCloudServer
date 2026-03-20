import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {defineConfig} from '@hey-api/openapi-ts';

const rootDir = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  input: resolve(rootDir, '../backend/openapi_doc/specs/openapi-v1.json'),
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
