import { useState } from "react";
import { Check, ExternalLink, MapPin, MapPinned, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRoadLocation } from "@/hooks/useRoadLocation";
import type { RoadLocation } from "@/types";

interface LocationPickerProps { value: RoadLocation | null; onChange: (location: RoadLocation | null) => void; }

export function LocationPicker({ value, onChange }: LocationPickerProps) {
  const [query, setQuery] = useState("");
  const { search, isSearching, mapsConfigured } = useRoadLocation();
  const choose = async () => { const next = await search(query); onChange(next); };
  return (
    <div data-testid="location-picker" className="location-surface rounded-[22px] p-4 sm:p-5">
      <div className="mb-4 flex items-start justify-between gap-3"><div><div className="flex items-center gap-2 text-sm font-semibold text-white"><MapPin size={15} className="text-[#b8e986]" /> Optional road location</div><p className="mt-1 text-xs leading-5 text-white/45">Attach coordinates and Street View context to this survey.</p></div><span className="rounded-full border border-white/10 px-2 py-1 text-[10px] uppercase tracking-[0.14em] text-white/35">Can skip</span></div>
      <div className="flex gap-2"><div className="relative flex-1"><Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/35" /><Input data-testid="location-search-input" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void choose(); }} placeholder="Search city, road or landmark" className="h-10 border-white/10 bg-white/[0.06] pl-9 text-sm text-white placeholder:text-white/30" /></div><Button data-testid="location-search-button" type="button" onClick={() => void choose()} disabled={isSearching} className="h-10 rounded-xl bg-[#b8e986] px-4 text-[#0d1917] hover:bg-[#d3f5ad]">{isSearching ? "Searching" : "Find"}</Button></div>
      {value ? <div data-testid="location-result-card" className="mt-4 overflow-hidden rounded-2xl border border-[#b8e986]/20 bg-[#b8e986]/[0.06]"><div className="map-preview relative h-28"><div className="map-grid absolute inset-0" /><div className="absolute left-[54%] top-[35%] flex h-7 w-7 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-[#b8e986] text-[#0b2118] shadow-[0_0_0_7px_rgba(184,233,134,0.16)]"><MapPin size={14} fill="currentColor" /></div><div className="absolute bottom-2 left-3 rounded-md bg-[#0d1917]/80 px-2 py-1 text-[10px] text-white/70">{value.latitude.toFixed(4)}° N · {value.longitude.toFixed(4)}° E</div></div><div className="flex items-center justify-between gap-3 p-3"><div><div className="text-sm font-medium text-white">{value.address}</div><div className="mt-1 flex items-center gap-1.5 text-[11px] text-white/50">{value.streetViewAvailable ? <><MapPinned size={12} className="text-[#b8e986]" /> Street View available</> : <><ExternalLink size={12} /> Map only · Street View unavailable</>}</div></div><Button data-testid="location-remove-button" type="button" variant="ghost" size="sm" onClick={() => onChange(null)} className="text-white/50 hover:text-white">Remove</Button></div></div> : <button type="button" data-testid="location-skip-button" onClick={() => onChange(null)} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-white/10 py-3 text-xs text-white/40 transition-colors hover:border-white/20 hover:text-white/70"><Check size={13} /> Continue without a location</button>}
      {!mapsConfigured && <div data-testid="maps-config-notice" className="mt-3 text-[10px] leading-4 text-white/30">Maps preview is in demo mode. Add <code className="text-white/50">VITE_GOOGLE_MAPS_API_KEY</code> to enable live Maps and Street View.</div>}
    </div>
  );
}
