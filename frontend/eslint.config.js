import js from '@eslint/js';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';

export default [
  { ignores: ['dist/**', 'node_modules/**', '*.config.js'] },
  js.configs.recommended,
  {
    files: ['src/**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: {
        ...globals.browser,
        ...globals.node,
        // v0.58i: build-time constant injected by vite.config.js define
        __MOIMIO_VERSION__: 'readonly',
      },
    },
    plugins: {
      react,
      'react-hooks': reactHooks,
    },
    settings: { react: { version: 'detect' } },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,

      // Standard rules
      'no-unused-vars': ['warn', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrors: 'none',
      }],
      'no-undef': 'error',

      // Allow `} catch { }` (fire-and-forget API calls).
      // We don't want it allowed for `if (x) { }` or `while () { }` etc., so
      // only enable allowEmptyCatch — other empty blocks remain errors.
      'no-empty': ['error', { allowEmptyCatch: true }],

      // React rules — turn off PropTypes (we don't use them) and noisy
      // stylistic rules that don't catch real bugs.
      'react/prop-types': 'off',
      'react/react-in-jsx-scope': 'off',
      'react/no-unescaped-entities': 'off',

      // React Hooks — keep the foundational rules on.
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // React Hooks v5 added several STRICTER rules that produce a lot of
      // noise on idiomatic React patterns. Turning them off until/unless
      // they prove their worth on this specific codebase.
      'react-hooks/immutability': 'off',           // Was flagging non-mutations as mutations
      'react-hooks/set-state-in-effect': 'off',    // Common idiom (sync prop → state)
      'react-hooks/preserve-manual-memoization': 'off',
      'react-hooks/static-components': 'off',
    },
  },
];
