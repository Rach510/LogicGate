import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, CircleUserRound, LogOut, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FloatingNavigation } from "@/components/navigation/FloatingNavigation";
import { IssueModal } from "@/components/issues/IssueModal";
import { AuthView } from "@/views/auth/AuthView";
import { OnboardingView } from "@/views/onboarding/OnboardingView";
import { ProcessingView } from "@/views/processing/ProcessingView";
import { DashboardView } from "@/views/dashboard/DashboardView";
import { VideoView } from "@/views/video/VideoView";
import { AnalyticsView } from "@/views/analytics/AnalyticsView";
import { BudgetsView } from "@/views/budgets/BudgetsView";
import { SettingsView } from "@/views/settings/SettingsView";
import { useAuth } from "@/hooks/useAuth";
import { useRoadRead } from "@/hooks/useRoadRead";
import { mockUser } from "@/data/mockData";
import type { AppView, Project, RoadLocation } from "@/types";

type AppStage = "auth" | "onboarding" | "processing" | "app";

export default function App() {
  const { user, signIn, signOut } = useAuth();
const { projects, activeProject, analytics, budget, video, bgImage, loadWorkspace, createProject } = useRoadRead();  const [stage, setStage] = useState<AppStage>("auth");
  const [view, setView] = useState<AppView>("dashboard");
  const [issueOpen, setIssueOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);

  const enterWorkspace = async (project: Project) => { await loadWorkspace(project); setStage("app"); setView("dashboard"); };
  const handleCreate = async (name: string, fileName: string, location: RoadLocation | null, file: File | null) => { setStage("processing"); await createProject(name, fileName, location, file); };
  const handleSignOut = () => { signOut(); setStage("auth"); setView("dashboard"); };
  const displayUser = user ?? mockUser;
  if (stage === "auth") return <AuthView onSubmit={(email) => { void signIn(email).then(() => setStage("onboarding")); }} />;
  if (stage === "onboarding") return <OnboardingView projects={projects} onExisting={(project) => { void enterWorkspace(project); }} onCreate={(name, fileName, location, file) => { void handleCreate(name, fileName, location, file); }} />;
  if (stage === "processing") return <ProcessingView onComplete={() => setStage("app")} />;
  if (!activeProject || !analytics || !budget || !video) return null;
  return <div data-testid="roadread-app" className="min-h-svh bg-[#08100f]"><FloatingNavigation activeView={view} onChange={setView} onAccount={() => setAccountOpen(true)} user={displayUser} /><AnimatePresence mode="wait"><motion.div key={view} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -5 }} transition={{ duration: 0.2 }}>
  {view === "dashboard" && <DashboardView project={activeProject} analytics={analytics} budget={budget} video={video} bgImage={bgImage} onVideo={() => setView("video")} onReport={() => setIssueOpen(true)} />}
  {view === "video" && <VideoView project={activeProject} video={video} bgImage={bgImage} onBack={() => setView("dashboard")} />}    {view === "analytics" && <AnalyticsView project={activeProject} analytics={analytics} budget={budget} video={video} onUpload={() => setStage("onboarding")} />}
    {view === "budgets" && <BudgetsView budget={budget} />}
    {view === "settings" && <SettingsView user={displayUser} onSignOut={handleSignOut} />}
  </motion.div></AnimatePresence><button type="button" data-testid="floating-report-issue-button" onClick={() => setIssueOpen(true)} className="fixed bottom-5 right-5 z-30 flex items-center gap-2 rounded-full border border-[#edb06c]/30 bg-[#241b13]/90 px-4 py-3 text-xs font-semibold text-[#ffd699] shadow-2xl backdrop-blur-xl transition-transform hover:-translate-y-0.5 active:scale-95"><span className="h-1.5 w-1.5 rounded-full bg-[#edb06c]" /> Report an issue</button><IssueModal open={issueOpen} onClose={() => setIssueOpen(false)} /><AnimatePresence>{accountOpen && <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 bg-black/45 backdrop-blur-sm" onClick={() => setAccountOpen(false)}><motion.aside initial={{ x: 360 }} animate={{ x: 0 }} exit={{ x: 360 }} transition={{ type: "spring", stiffness: 360, damping: 32 }} onClick={(event) => event.stopPropagation()} data-testid="account-drawer" className="absolute right-0 top-0 flex h-full w-full max-w-sm flex-col border-l border-white/10 bg-[#13201d]/95 p-6 shadow-2xl backdrop-blur-2xl"><div className="flex items-center justify-between"><div><span className="section-kicker">Account</span><h2 className="mt-2 text-2xl font-semibold tracking-tight">Your workspace</h2></div><button type="button" data-testid="account-drawer-close-button" onClick={() => setAccountOpen(false)} className="text-white/45 hover:text-white"><X size={18} /></button></div><div className="mt-10 flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4"><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#b8e986] font-semibold text-[#10201b]">{displayUser.initials}</div><div><div className="text-sm font-medium">{displayUser.name}</div><div className="mt-1 text-xs text-white/40">{displayUser.email}</div></div></div><div className="mt-6 text-[10px] uppercase tracking-[0.18em] text-white/35">Switch account</div><div className="mt-3 space-y-2">{[mockUser, { ...mockUser, id: "user-priya", name: "Priya Shah", email: "priya@urbanworks.in", organization: "UrbanWorks India", initials: "PS" }].map((account) => <button key={account.id} type="button" data-testid={`account-switch-${account.id}-button`} onClick={() => setAccountOpen(false)} className="flex w-full items-center gap-3 rounded-xl border border-transparent p-3 text-left transition-colors hover:border-white/10 hover:bg-white/[0.05]"><span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 text-xs font-semibold">{account.initials}</span><span className="flex-1"><span className="block text-xs font-medium">{account.name}</span><span className="mt-1 block text-[10px] text-white/35">{account.organization}</span></span>{account.id === displayUser.id ? <span className="h-1.5 w-1.5 rounded-full bg-[#b8e986]" /> : <ArrowRight size={13} className="text-white/25" />}</button>)}</div><div className="mt-auto space-y-2"><Button data-testid="account-settings-button" type="button" variant="outline" onClick={() => { setView("settings"); setAccountOpen(false); }} className="h-11 w-full justify-between rounded-xl border-white/10 bg-white/[0.04] text-xs text-white/70 hover:bg-white/10">Account settings <CircleUserRound size={15} /></Button><Button data-testid="account-signout-button" type="button" variant="ghost" onClick={handleSignOut} className="h-11 w-full justify-start rounded-xl text-xs text-white/40 hover:text-[#edb06c]"><LogOut size={15} /> Sign out</Button></div></motion.aside></motion.div>}</AnimatePresence></div>;
}
