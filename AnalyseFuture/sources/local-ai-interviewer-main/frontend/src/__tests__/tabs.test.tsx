import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";
import { TabPanel, Tabs } from "../components/ui";

function Demo() {
  const [v, setV] = useState<"a" | "b" | "c">("a");
  return <><Tabs idBase="t" label="Sections" value={v} onChange={setV} tabs={[{ id: "a", label: "Alpha" }, { id: "b", label: "Beta" }, { id: "c", label: "Gamma" }]} />
    {(["a", "b", "c"] as const).map((x) => <TabPanel key={x} idBase="t" id={x} active={v === x}>panel {x}</TabPanel>)}</>;
}

describe("Tabs", () => {
  it("follows the tabs pattern: roles, aria-selected, aria-controls, roving tabindex, only the selected panel visible", () => {
    render(<Demo />);
    expect(screen.getByRole("tablist", { name: "Sections" })).toBeInTheDocument();
    const alpha = screen.getByRole("tab", { name: "Alpha" }), beta = screen.getByRole("tab", { name: "Beta" });
    expect(alpha).toHaveAttribute("aria-selected", "true"); expect(beta).toHaveAttribute("aria-selected", "false");
    expect(alpha).toHaveAttribute("tabindex", "0"); expect(beta).toHaveAttribute("tabindex", "-1");
    expect(alpha.getAttribute("aria-controls")).toBe("t-panel-a");
    expect(screen.getByRole("tabpanel", { name: "Alpha" })).toHaveTextContent("panel a");
    expect(screen.queryByRole("tabpanel", { name: "Beta" })).toBeNull();      // hidden panels are not exposed
  });
  it("arrow keys, Home and End move the selection and the focus", () => {
    render(<Demo />);
    const alpha = screen.getByRole("tab", { name: "Alpha" });
    alpha.focus();
    fireEvent.keyDown(alpha, { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: "Beta" })).toHaveAttribute("aria-selected", "true"); expect(screen.getByRole("tab", { name: "Beta" })).toHaveFocus();
    fireEvent.keyDown(screen.getByRole("tab", { name: "Beta" }), { key: "End" });
    expect(screen.getByRole("tab", { name: "Gamma" })).toHaveFocus();
    fireEvent.keyDown(screen.getByRole("tab", { name: "Gamma" }), { key: "ArrowRight" });
    expect(screen.getByRole("tab", { name: "Alpha" })).toHaveFocus();       // wraps
    fireEvent.keyDown(screen.getByRole("tab", { name: "Alpha" }), { key: "ArrowLeft" });
    expect(screen.getByRole("tab", { name: "Gamma" })).toHaveAttribute("aria-selected", "true");
  });
});
