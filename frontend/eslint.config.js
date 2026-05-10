// Flat config for ESLint 9.x. 与 .eslintrc.cjs 等价，已迁移到新格式。
import js from "@eslint/js";
import vue from "eslint-plugin-vue";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import vueParser from "vue-eslint-parser";
import globals from "globals";

export default [
  {
    ignores: ["dist/**", "node_modules/**", "coverage/**", "*.d.ts", "*.mjs"],
  },
  js.configs.recommended,
  ...vue.configs["flat/recommended"],
  {
    files: ["src/**/*.{ts,tsx,vue}", "*.ts", "*.cts", "*.mts"],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tsParser,
        ecmaVersion: 2024,
        sourceType: "module",
        extraFileExtensions: [".vue"],
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
    },
    rules: {
      ...tseslint.configs.recommended.rules,
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      // ESLint 9 引入的 no-useless-assignment 与 Vue <script setup> 模板间引用冲突
      "no-useless-assignment": "off",
      "vue/multi-word-component-names": "off",
      "vue/component-name-in-template-casing": ["error", "PascalCase"],
      "vue/component-definition-name-casing": ["error", "PascalCase"],
      // 我们用 TS 接口标 ? 即代表 optional，无需再要求 default
      "vue/require-default-prop": "off",
      "@typescript-eslint/explicit-module-boundary-types": "off",
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/consistent-type-imports": "error",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
    },
  },
];
