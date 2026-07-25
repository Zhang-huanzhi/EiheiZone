import { describe, expect, it } from "vitest";

import {
  getRoleHome,
  getSafePostLoginPath,
} from "@/features/auth/auth-routing";

describe("auth routing", () => {
  it("returns each role home", () => {
    expect(getRoleHome("family")).toBe("/family");
    expect(getRoleHome("owner")).toBe("/owner");
  });

  it("keeps an allowed protected path", () => {
    expect(getSafePostLoginPath("/family/posts/1", "family")).toBe(
      "/family/posts/1",
    );
    expect(getSafePostLoginPath("/owner/posts", "owner")).toBe("/owner/posts");
  });

  it("does not send Family users into the Owner area", () => {
    expect(getSafePostLoginPath("/owner", "family")).toBe("/family");
  });

  it("rejects external and malformed redirect targets", () => {
    expect(getSafePostLoginPath("https://example.com", "owner")).toBe("/owner");
    expect(getSafePostLoginPath("/family\\..\\owner", "owner")).toBe("/owner");
  });
});
