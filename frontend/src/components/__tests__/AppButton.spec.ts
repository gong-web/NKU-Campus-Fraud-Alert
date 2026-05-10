import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AppButton from "../AppButton.vue";

describe("AppButton", () => {
  it("renders default slot", () => {
    const w = mount(AppButton, { slots: { default: "确认" } });
    expect(w.text()).toContain("确认");
  });

  it("emits click", async () => {
    const w = mount(AppButton);
    await w.trigger("click");
    expect(w.emitted("click")).toHaveLength(1);
  });

  it("disables on loading", () => {
    const w = mount(AppButton, { props: { loading: true } });
    const btn = w.get("button");
    expect(btn.attributes("disabled")).toBeDefined();
    expect(btn.attributes("aria-busy")).toBe("true");
  });

  it("respects danger variant class", () => {
    const w = mount(AppButton, { props: { variant: "danger" } });
    expect(w.classes()).toContain("app-btn--danger");
  });
});
