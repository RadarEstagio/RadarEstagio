import eslint from "@eslint/js";
import globals from "globals";

export default [
  { ignores: ["dist/**", "assets/**", "config.js"] },
  eslint.configs.recommended,
  {
    files: ["**/*.{js,mjs}"],
    languageOptions: { ecmaVersion: "latest", sourceType: "module", globals: globals.node },
  },
];
