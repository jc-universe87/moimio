/**
 * Vitest configuration — v1.0.0h-3.
 *
 * Co-exists with vite.config.js (which is for builds and dev server).
 * Tests use jsdom so React components can render with a fake DOM and
 * @testing-library can query it.
 *
 * Run: `npm test` (single pass) or `npm run test:watch` (continuous).
 * Coverage: `npm run test:coverage` (writes to coverage/).
 *
 * Tests live next to the source they cover, named `<file>.test.jsx`.
 * That keeps discovery automatic and makes it obvious which source
 * lacks coverage.
 */
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.js'],
    // Co-locate tests with source.
    include: ['src/**/*.test.{js,jsx}'],
    // Don't run on the production build output.
    exclude: ['node_modules', 'dist', '.git'],
    // Reset module + DOM state between tests so one test's render or
    // mock can't leak into the next. Without this, the React fake
    // tree accumulates and tests become order-dependent.
    clearMocks: true,
    restoreMocks: true,
  },
});
