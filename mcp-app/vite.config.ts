import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";
import { resolve } from "path";

export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    outDir: "dist/apps",
    rollupOptions: {
      input: {
        conversation: resolve(__dirname, "apps/conversation.html"),
        lessons: resolve(__dirname, "apps/lessons.html"),
        progress: resolve(__dirname, "apps/progress.html"),
      },
    },
  },
});
