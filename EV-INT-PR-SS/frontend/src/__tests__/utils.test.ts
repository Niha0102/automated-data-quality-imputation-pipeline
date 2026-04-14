import { describe, it, expect } from "vitest";
import { cn } from "@/lib/utils";

describe("cn utility", () => {
  it("merges class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "visible")).toBe("base visible");
  });

  it("deduplicates tailwind classes", () => {
    const result = cn("px-2", "px-4");
    expect(result).toBe("px-4");
  });

  it("handles undefined and null", () => {
    expect(cn("a", undefined, null as any, "b")).toBe("a b");
  });
});
