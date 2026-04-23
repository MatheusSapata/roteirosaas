import api from "./api";
import type { FlightSectionJourney, FlightSectionSegment } from "../types/page";

export interface FlightJourneysResponse {
  journeys: FlightSectionJourney[];
  lookup_available: boolean;
}

export interface FlightLookupResponse {
  provider: string;
  from_cache: boolean;
  message: string;
  flight: {
    flight_number?: string | null;
    flight_iata?: string | null;
    flight_icao?: string | null;
    airline_name?: string | null;
    airline_iata?: string | null;
    airline_icao?: string | null;
    airline_logo_url?: string | null;
    departure?: {
      iata?: string | null;
      airport?: string | null;
      city?: string | null;
      country?: string | null;
      terminal?: string | null;
      gate?: string | null;
      datetime?: string | null;
    };
    arrival?: {
      iata?: string | null;
      airport?: string | null;
      city?: string | null;
      country?: string | null;
      terminal?: string | null;
      gate?: string | null;
      datetime?: string | null;
    };
    duration_minutes?: number | null;
    status?: string | null;
  };
}

export interface FlightApiKey {
  id: number;
  provider: string;
  label: string;
  key_masked: string;
  is_active: boolean;
  status: "active" | "paused" | "exhausted" | "error";
  priority: number;
  monthly_limit: number;
  monthly_usage_estimated: number;
  total_usage_estimated: number;
  last_used_at?: string | null;
  last_error?: string | null;
  reset_day?: number | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface FlightApiKeysResponse {
  items: FlightApiKey[];
  summary: {
    provider: string;
    active_keys: number;
    monthly_usage_estimated: number;
    monthly_limit: number;
    last_used_at?: string | null;
  };
}

const flightSectionBase = (pageId: number | string, sectionId: string) =>
  `/admin/pages/${pageId}/sections/${encodeURIComponent(sectionId)}`;

export const getFlightJourneys = async (pageId: number | string, sectionId: string) => {
  const response = await api.get<FlightJourneysResponse>(`${flightSectionBase(pageId, sectionId)}/flight-journeys`);
  return response.data;
};

export const bootstrapFlightJourneys = async (pageId: number | string, sectionId: string) => {
  const response = await api.post<FlightJourneysResponse>(`${flightSectionBase(pageId, sectionId)}/flight-journeys/bootstrap`);
  return response.data;
};

export const createFlightJourney = async (
  pageId: number | string,
  sectionId: string,
  payload: Partial<FlightSectionJourney>
) => {
  const response = await api.post<FlightJourneysResponse>(`${flightSectionBase(pageId, sectionId)}/flight-journeys`, payload);
  return response.data;
};

export const updateFlightJourney = async (
  pageId: number | string,
  sectionId: string,
  journeyId: number,
  payload: Partial<FlightSectionJourney>
) => {
  const response = await api.patch<FlightJourneysResponse>(
    `${flightSectionBase(pageId, sectionId)}/flight-journeys/${journeyId}`,
    payload
  );
  return response.data;
};

export const deleteFlightJourney = async (pageId: number | string, sectionId: string, journeyId: number) => {
  const response = await api.delete<FlightJourneysResponse>(`${flightSectionBase(pageId, sectionId)}/flight-journeys/${journeyId}`);
  return response.data;
};

export const reorderFlightJourneys = async (
  pageId: number | string,
  sectionId: string,
  journeyIds: number[]
) => {
  const response = await api.post<FlightJourneysResponse>(
    `${flightSectionBase(pageId, sectionId)}/flight-journeys/reorder`,
    { journey_ids: journeyIds }
  );
  return response.data;
};

export const createFlightSegment = async (
  pageId: number | string,
  sectionId: string,
  payload: Partial<FlightSectionSegment> & { journey_id: number }
) => {
  const response = await api.post<FlightJourneysResponse>(`${flightSectionBase(pageId, sectionId)}/flight-segments`, payload);
  return response.data;
};

export const updateFlightSegment = async (
  pageId: number | string,
  sectionId: string,
  segmentId: number,
  payload: Partial<FlightSectionSegment>
) => {
  const response = await api.patch<FlightJourneysResponse>(
    `${flightSectionBase(pageId, sectionId)}/flight-segments/${segmentId}`,
    payload
  );
  return response.data;
};

export const deleteFlightSegment = async (pageId: number | string, sectionId: string, segmentId: number) => {
  const response = await api.delete<FlightJourneysResponse>(`${flightSectionBase(pageId, sectionId)}/flight-segments/${segmentId}`);
  return response.data;
};

export const reorderFlightSegments = async (
  pageId: number | string,
  sectionId: string,
  journeyId: number,
  segmentIds: number[]
) => {
  const response = await api.post<FlightJourneysResponse>(
    `${flightSectionBase(pageId, sectionId)}/flight-segments/reorder`,
    { journey_id: journeyId, segment_ids: segmentIds }
  );
  return response.data;
};

export const lookupFlight = async (
  pageId: number | string,
  sectionId: string,
  payload: {
    flight_number: string;
    flight_date: string;
    journey_id?: number;
    segment_id?: number;
  }
) => {
  const response = await api.post<FlightLookupResponse>(`${flightSectionBase(pageId, sectionId)}/flight-lookup`, payload);
  return response.data;
};

const flightApiKeyBase = "/admin/master/flight-api-keys";

export const listFlightApiKeys = async () => {
  const response = await api.get<FlightApiKeysResponse>(flightApiKeyBase);
  return response.data;
};

export const createFlightApiKey = async (payload: {
  provider?: string;
  label: string;
  api_key: string;
  is_active?: boolean;
  status?: string;
  priority?: number;
  monthly_limit?: number;
  reset_day?: number | null;
  notes?: string;
}) => {
  const response = await api.post<FlightApiKey>(flightApiKeyBase, payload);
  return response.data;
};

export const updateFlightApiKey = async (
  id: number,
  payload: Partial<{
    label: string;
    api_key: string;
    is_active: boolean;
    status: string;
    priority: number;
    monthly_limit: number;
    reset_day: number | null;
    notes: string;
  }>
) => {
  const response = await api.patch<FlightApiKey>(`${flightApiKeyBase}/${id}`, payload);
  return response.data;
};

export const testFlightApiKey = async (id: number) => {
  const response = await api.post<{ detail: string }>(`${flightApiKeyBase}/${id}/test`);
  return response.data;
};

export const pauseFlightApiKey = async (id: number) => {
  const response = await api.post<FlightApiKey>(`${flightApiKeyBase}/${id}/pause`);
  return response.data;
};

export const activateFlightApiKey = async (id: number) => {
  const response = await api.post<FlightApiKey>(`${flightApiKeyBase}/${id}/activate`);
  return response.data;
};

export const resetFlightApiKeyUsage = async (id: number) => {
  const response = await api.post<FlightApiKey>(`${flightApiKeyBase}/${id}/reset-usage`);
  return response.data;
};

export const deleteFlightApiKey = async (id: number) => {
  const response = await api.delete<{ detail: string }>(`${flightApiKeyBase}/${id}`);
  return response.data;
};
