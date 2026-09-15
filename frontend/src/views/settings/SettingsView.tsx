import { useEffect, useState } from "react";
import { ArrowLeft, Building2, Check, ChevronRight, CircleUserRound, CreditCard, Mail, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { User } from "@/types";

interface SettingsViewProps { user: User; onSignOut: () => void; }
type Plan = "Essentials" | "Professional" | "Enterprise";

const plans: Array<{ name: Plan; price: string; copy: string; features: string[]; recommended?: boolean }> = [
  { name: "Essentials", price: "₹8,900", copy: "For focused site teams", features: ["5 projects", "Basic road analytics", "CSV exports"] },
  { name: "Professional", price: "₹24,900", copy: "For teams moving at scale", features: ["Unlimited projects", "Computer vision overlays", "Budget intelligence"], recommended: true },
  { name: "Enterprise", price: "Custom", copy: "For connected programs", features: ["Multi-org controls", "Dedicated model review", "API access"] },
];

export function SettingsView({ user, onSignOut }: SettingsViewProps) {
  const [currentPlan, setCurrentPlan] = useState<Plan>(() => {
    if (typeof window === "undefined") return "Professional";
    return (localStorage.getItem("roadread-plan") as Plan | null) ?? "Professional";
  });
  const [paymentPlan, setPaymentPlan] = useState<Plan | null>(null);

  useEffect(() => { localStorage.setItem("roadread-plan", currentPlan); }, [currentPlan]);

  if (paymentPlan) {
    const plan = plans.find((item) => item.name === paymentPlan)!;
    return (
      <main data-testid="payment-screen" className="app-screen min-h-svh bg-[#08100f] px-4 pb-10 pt-20 text-white sm:px-8 sm:pt-24">
        <div className="mx-auto max-w-[1000px]">
          <button type="button" data-testid="payment-back-button" onClick={() => setPaymentPlan(null)} className="mb-10 flex items-center gap-2 text-xs text-white/45 hover:text-white">
            <ArrowLeft size={14} /> Back to plans
          </button>
          <header className="mb-8">
            <p className="section-kicker text-[#b8e986]">Secure checkout · Demo</p>
            <h1 data-testid="payment-heading" className="mt-2 text-4xl font-semibold tracking-[-0.06em] sm:text-6xl">Activate {plan.name}</h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-white/40">This is a demo payment page. No payment is processed and no card details are stored.</p>
          </header>
          <div className="grid gap-5 lg:grid-cols-[1.25fr_0.75fr]">
            <section className="glass-panel rounded-[26px] p-5 sm:p-7">
              <div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#b8e986]/10 text-[#b8e986]"><CreditCard size={18} /></span><div><span className="section-kicker">Payment details</span><h2 className="mt-1 text-lg font-semibold">Demo checkout</h2></div></div>
              <div className="mt-7 grid gap-4">
                <label className="block"><span className="mb-2 block text-xs text-white/55">Card number</span><input data-testid="payment-card-input" placeholder="•••• •••• •••• ••••" className="h-12 w-full rounded-xl border border-white/10 bg-white/[0.05] px-4 text-sm text-white outline-none focus:border-[#b8e986]/50" /></label>
                <div className="grid grid-cols-2 gap-4"><label className="block"><span className="mb-2 block text-xs text-white/55">Expiry</span><input data-testid="payment-expiry-input" placeholder="MM / YY" className="h-12 w-full rounded-xl border border-white/10 bg-white/[0.05] px-4 text-sm text-white outline-none focus:border-[#b8e986]/50" /></label><label className="block"><span className="mb-2 block text-xs text-white/55">CVV</span><input data-testid="payment-cvv-input" placeholder="•••" className="h-12 w-full rounded-xl border border-white/10 bg-white/[0.05] px-4 text-sm text-white outline-none focus:border-[#b8e986]/50" /></label></div>
                <div className="rounded-xl border border-[#b8e986]/15 bg-[#b8e986]/[0.05] p-4 text-xs leading-5 text-white/45">For this hackathon demo, the fields above are visual only. Click confirm to simulate a successful checkout.</div>
              </div>
              <Button data-testid="payment-confirm-button" type="button" onClick={() => { setCurrentPlan(plan.name); setPaymentPlan(null); }} className="mt-6 h-12 w-full rounded-xl bg-[#b8e986] text-[#10201b] hover:bg-[#d3f5ad]">Confirm & activate plan <ChevronRight size={16} /></Button>
            </section>
            <aside className="glass-panel rounded-[26px] p-5 sm:p-7"><span className="section-kicker">Order summary</span><div className="mt-5 flex items-start justify-between gap-4"><div><h2 className="text-xl font-semibold">{plan.name}</h2><p className="mt-1 text-xs text-white/40">{plan.copy}</p></div><span className="text-xl font-semibold">{plan.price}{plan.price !== "Custom" && <small className="ml-1 text-xs text-white/35">/ mo</small>}</span></div><div className="mt-6 space-y-3 border-t border-white/10 pt-5">{plan.features.map((feature) => <div key={feature} className="flex items-center gap-2 text-xs text-white/60"><Check size={13} className="text-[#b8e986]" /> {feature}</div>)}</div></aside>
          </div>
        </div>
      </main>
    );
  }

  return <main data-testid="settings-screen" className="app-screen min-h-svh bg-[#08100f] px-4 pb-10 pt-20 text-white sm:px-8 sm:pt-24"><div className="mx-auto max-w-[1000px]"><header className="mb-10"><p className="section-kicker text-[#b8e986]">Workspace control</p><h1 data-testid="settings-heading" className="mt-2 text-4xl font-semibold tracking-[-0.06em] sm:text-6xl">Settings</h1><p className="mt-3 text-sm text-white/40">Your people, plan and model preferences in one quiet place.</p></header><section data-testid="settings-profile-section" className="glass-panel rounded-[26px] p-5 sm:p-7"><div className="flex flex-wrap items-center justify-between gap-4"><div className="flex items-center gap-4"><div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#b8e986] text-xl font-semibold text-[#10201b]">{user.initials}</div><div><h2 className="text-lg font-semibold">{user.name}</h2><p className="mt-1 text-xs text-white/40">{user.role} · {user.organization}</p></div></div><Badge variant="outline" className="border-[#b8e986]/30 text-[#cbedab]"><ShieldCheck size={12} /> Verified workspace</Badge></div><div className="mt-8 grid gap-3 sm:grid-cols-3"><div className="settings-field"><Mail size={14} className="text-white/30" /><div><span className="block text-[10px] uppercase tracking-[0.14em] text-white/30">Email</span><span className="mt-1 block text-xs text-white/75">{user.email}</span></div></div><div className="settings-field"><Building2 size={14} className="text-white/30" /><div><span className="block text-[10px] uppercase tracking-[0.14em] text-white/30">Organization</span><span className="mt-1 block text-xs text-white/75">{user.organization}</span></div></div><div className="settings-field"><CircleUserRound size={14} className="text-white/30" /><div><span className="block text-[10px] uppercase tracking-[0.14em] text-white/30">Role</span><span className="mt-1 block text-xs text-white/75">{user.role}</span></div></div></div></section><section data-testid="settings-pricing-section" className="mt-5"><div className="mb-4 flex items-end justify-between"><div><span className="section-kicker">Pricing</span><h2 className="mt-2 text-2xl font-semibold tracking-tight">Choose your operating rhythm</h2></div><span className="text-xs text-white/35">Monthly · cancel anytime</span></div><div className="grid gap-3 md:grid-cols-3">{plans.map((plan) => { const isCurrent = currentPlan === plan.name; return <div key={plan.name} className={`pricing-option ${plan.recommended ? "pricing-highlight" : ""}`}>{plan.recommended && <Badge className="absolute right-4 top-4 bg-[#b8e986] text-[9px] text-[#10201b]">Recommended</Badge>}<span className="text-sm font-semibold">{plan.name}</span><span className="mt-4 block text-3xl font-semibold tracking-[-0.06em]">{plan.price}<small className="ml-1 text-xs font-normal text-white/35">{plan.price === "Custom" ? "" : "/ mo"}</small></span><span className="mt-2 block text-xs text-white/40">{plan.copy}</span><div className="mt-6 space-y-3 border-t border-white/10 pt-5">{plan.features.map((feature) => <div key={feature} className="flex items-center gap-2 text-xs text-white/60"><Check size={13} className="text-[#b8e986]" /> {feature}</div>)}</div><Button data-testid={`settings-${plan.name.toLowerCase()}-button`} type="button" variant={isCurrent ? "default" : "outline"} onClick={() => { if (!isCurrent) setPaymentPlan(plan.name); }} className={`mt-7 h-10 w-full rounded-xl text-xs ${isCurrent ? "bg-[#b8e986] text-[#10201b] hover:bg-[#d3f5ad]" : "border-white/10 bg-white/[0.04] text-white/70 hover:bg-white/10"}`}>{isCurrent ? "Current plan" : plan.name === "Enterprise" ? "Select plan" : "Select plan"}<ChevronRight size={14} /></Button></div>; })}</div></section><Button data-testid="settings-signout-button" type="button" onClick={onSignOut} variant="ghost" className="mt-8 text-xs text-white/40 hover:text-[#edb06c]">Sign out of this demo session</Button></div></main>;
}
