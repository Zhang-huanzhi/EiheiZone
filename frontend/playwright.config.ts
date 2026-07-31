import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  reporter: [
    ["list"],
    ["html", { open: "never" }],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000",
    channel: "chrome",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
});
