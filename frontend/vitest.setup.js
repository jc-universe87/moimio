/**
 * Vitest setup — runs once before any tests.
 *
 * Loads @testing-library/jest-dom's matchers (toBeInTheDocument,
 * toHaveTextContent, etc.) into Vitest's expect. Also adds a global
 * afterEach that unmounts React trees so tests don't accumulate
 * orphaned DOM nodes across the suite.
 */
import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

afterEach(() => {
  cleanup();
});
