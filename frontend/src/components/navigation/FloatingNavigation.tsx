import { AnimatePresence, motion } from "motion/react";
import { BarChart3, ChevronRight, CircleUserRound, Gauge, Menu, Settings2, WalletCards, X } from "lucide-react";
import type { AppView, User } from "@/types";

const items: Array<{ id: AppView; label: string; icon: typeof Gauge; detail: string }> = [
  { id: "dashboard", label: "Dashboard", icon: Gauge, detail: "Live overview" },
  { id: "video", label: "Video analysis", icon: Menu, detail: "Frame-by-frame" },
  { id: "analytics", label: "Analytics", icon: BarChart3, detail: "Road condition" },
  { id: "budgets", label: "Budgets", icon: WalletCards, detail: "Cost planning" },
  { id: "settings", label: "Settings", icon: Settings2, detail: "Workspace" },
];

interface FloatingNavigationProps {
  activeView: AppView;
  onChange: (view: AppView) => void;
  onAccount: () => void;
  user: User;
}

export function FloatingNavigation({ activeView, onChange, onAccount, user }: FloatingNavigationProps) {
  const [open, setOpen] = useState(false);
  return (
    <div className="pointer-events-none fixed left-5 top-5 z-40 sm:left-8 sm:top-7">
      <div className="pointer-events-auto flex items-center gap-3">
        <button
          type="button"
          data-testid="navigation-menu-toggle-button"
          aria-label={open ? "Close navigation" : "Open navigation"}
          aria-expanded={open}
          onClick={() => setOpen((current) => !current)}
          className="glass-control flex h-11 w-11 items-center justify-center rounded-2xl text-white shadow-2xl transition-transform active:scale-95"
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
        <div data-testid="roadread-brand-mark" className="flex items-center gap-2 text-white">
          <span className="brand-mark">R</span>
          <span className="text-[13px] font-semibold tracking-[0.24em]">ROADREAD</span>
        </div>
      </div>
      <AnimatePresence initial={false}>
        {open && (
          <motion.nav
            initial={{ opacity: 0, scale: 0.92, y: -8, transformOrigin: "18px 10px" }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: -5 }}
            transition={{ type: "spring", stiffness: 420, damping: 32 }}
            data-testid="navigation-panel"
            className="glass-panel pointer-events-auto mt-3 w-[250px] rounded-[24px] p-2.5 shadow-2xl"
          >
            <div className="px-3 pb-2 pt-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/40">Workspace</div>
            {items.map(({ id, label, icon: Icon, detail }) => (
              <button
                key={id}
                type="button"
                data-testid={`navigation-${id}-button`}
                onClick={() => { onChange(id); setOpen(false); }}
                className={`nav-item ${activeView === id ? "nav-item-active" : ""}`}
              >
                <span className="nav-icon"><Icon size={16} strokeWidth={1.8} /></span>
                <span className="flex-1 text-left"><span className="block text-[13px] font-medium">{label}</span><span className="block text-[10px] text-white/40">{detail}</span></span>
                {activeView === id && <span className="h-1.5 w-1.5 rounded-full bg-[#b8e986]" />}
              </button>
            ))}
            <div className="my-2 border-t border-white/10" />
            <button type="button" data-testid="navigation-account-button" onClick={() => { onAccount(); setOpen(false); }} className="nav-item">
              <span className="nav-icon bg-white/10"><CircleUserRound size={16} strokeWidth={1.8} /></span>
              <span className="flex-1 text-left"><span className="block text-[13px] font-medium">{user.name}</span><span className="block text-[10px] text-white/40">{user.organization}</span></span>
              <ChevronRight size={14} className="text-white/30" />
            </button>
          </motion.nav>
        )}
      </AnimatePresence>
    </div>
  );
}

function useState(initial: boolean) {
  return requireReactUseState(initial);
}

// Kept local to avoid exporting a state helper as part of the navigation API.
import { useState as requireReactUseState } from "react";
