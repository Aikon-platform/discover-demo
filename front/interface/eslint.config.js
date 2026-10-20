import js from "@eslint/js";
import globals from "globals";
import json from "@eslint/json";
import css from "@eslint/css";
import svelte from "eslint-plugin-svelte";
import svelteParser from "svelte-eslint-parser";
import ts from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import { defineConfig, globalIgnores } from "eslint/config";
import stylistic from "@stylistic/eslint-plugin";

const baseRules = {
    "no-unused-vars": "off",
    "no-undef": "error",
    "quotes": "off",
    "prefer-const": [ "error", {
        "destructuring": "all",
    }],
    "@stylistic/indent": [ "warn", 4 ],
    "space-in-parens": [ "error", "never" ],
    "array-bracket-spacing": [ "error", "always", { objectsInArrays: false, arraysInArrays: false }],
    "@stylistic/object-curly-spacing": [ "error", "always", { objectsInObjects: true, arraysInObjects: true }]
};

export default defineConfig([
    {
        files: [ "**/*.{js,mjs,cjs}" ],
        plugins: {
            "@stylistic": stylistic,
            js,
        },
        extends: [ "js/recommended" ],
        languageOptions: {
            globals: { ...globals.browser, ...globals.node },
        },
        rules: baseRules,
    },
    {
        files: [ "**/*.svelte", "**/*.svelte.js" ],
        plugins: {
            "@stylistic": stylistic,
            svelte,
        },
        extends: [ "svelte/recommended" ],
        languageOptions: {
            // parses the Svelte file structure
            parser: svelteParser,
            parserOptions: {
                // parses the <script> block contents
                parser: tsParser,
                extraFileExtensions: [ ".svelte" ],
            },
            globals: { ...globals.browser, ...globals.node },
        },
        rules: {
            ...baseRules,
            "svelte/require-each-key": "off",
            "svelte/no-at-html-tags": "warn",
            "svelte/prefer-svelte-reactivity": "warn",
            "svelte/prefer-writable-derived": "warn"
        },
    },
    {
        files: [ "**/*.json" ],
        plugins: { json },
        language: "json/jsonc",  // jsonc = json with comments
        extends: [ "json/recommended" ],
    },
    {
        files: [ "**/*.css" ],
        plugins: { css },
        language: "css/css",
        extends: [ "css/recommended" ],
    },
    globalIgnores([ "package-lock.json" ]),
]);
