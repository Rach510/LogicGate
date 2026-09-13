import type { RoadLocation } from "@/types";

const configuredKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string | undefined;

// TODO: Connect to Google Maps JavaScript API when VITE_GOOGLE_MAPS_API_KEY is configured
export const mapsApi = {
  isConfigured: Boolean(configuredKey),
  search: async (query: string): Promise<RoadLocation> => ({ latitude: 13.3409, longitude: 74.7421, address: query || "Udupi, Karnataka", heading: 122, streetViewAvailable: Boolean(configuredKey), panoramaId: configuredKey ? "configured-panorama" : undefined }),
};
