import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";
import { resolve } from "path";

// vite-plugin-singlefile requires single-entry builds.
// Use VITE_APP env var to select which app to build.
const appName = process.env.VITE_APP || "progress";

export default defineConfig({
  root: resolve(__dirname, "apps"),
  plugins: [viteSingleFile()],
  build: {
    outDir: resolve(__dirname, "dist/apps"),
    emptyOutDir: false,
    rollupOptions: {
      input: resolve(__dirname, `apps/${appName}.html`),
    },
  },
});
