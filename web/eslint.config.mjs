import eslint from "@eslint/js";
import globals from "globals";

export default [
  { ignores: ["dist/**", "assets/**", "config.js"] },
  eslint.configs.recommended,
  {
    files: ["**/*.{js,mjs,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: { ...globals.browser, ...globals.node },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      "no-empty": ["error", { allowEmptyCatch: true }],
    },
  },
  {
    files: ["**/*.jsx"],
    rules: {
      "no-unused-vars": ["error", { varsIgnorePattern: "^[A-Z]" }],
    },
  },
];
