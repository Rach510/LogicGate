import { useCallback, useState } from "react";
import { mapsApi } from "@/api/maps";
import type { RoadLocation } from "@/types";

export function useRoadLocation() {
  const [location, setLocation] = useState<RoadLocation | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const search = useCallback(async (query: string) => {
    setIsSearching(true);
    const result = await mapsApi.search(query);
    setLocation(result);
    setIsSearching(false);
    return result;
  }, []);
  return { location, setLocation, search, isSearching, mapsConfigured: mapsApi.isConfigured };
}
