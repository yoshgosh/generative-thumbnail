// @ts-check
import { defineConfig, globalIgnores } from 'eslint/config';
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import eslintConfigPrettier from 'eslint-config-prettier';

export default defineConfig([
    globalIgnores(['dist/**', 'node_modules/**']),

    eslint.configs.recommended,
    ...tseslint.configs.recommended,
    eslintConfigPrettier,

    {
        files: ['src/**/*.ts', 'src/**/*.tsx'],
        rules: {
            // any の使用はエラーではなく警告に変更
            '@typescript-eslint/no-explicit-any': 'warn',
            // 未使用の引数はエラーではなく警告に変更、_で始まる引数は無視
            '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
            // Azure Functions では context.log を使うが console も許容
            'no-console': 'off',
        },
    },
]);
