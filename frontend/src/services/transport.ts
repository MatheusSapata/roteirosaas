import api from "./api";
import type {
  SeatAdminAssignmentPayload,
  SeatAssignmentPayload,
  SeatBlockPayload,
  SeatHistoryResponse,
  SeatMapContext,
  SeatPostSignatureStatus,
  SeatSelectionContext,
  TripTransportConfigOut,
  TripTransportConfigPayload,
  VehicleLayoutDetail,
  VehicleLayoutListResponse,
  VehicleLayoutPayload,
  VehicleListResponse,
  VehicleOut,
  VehiclePayload,
} from "../types/transport";

export const getPostSignatureSeatStatus = (token: string) =>
  api.get<SeatPostSignatureStatus>(`/public/transport/signatures/${token}/status`);

export const getPublicSeatSelectionContext = (token: string, tripVehicleId?: number) =>
  api.get<SeatSelectionContext>(`/public/transport/signatures/${token}/seats`, {
    params: tripVehicleId ? { trip_vehicle_id: tripVehicleId } : undefined,
  });

export const selectSeatForSignature = (token: string, payload: SeatAssignmentPayload) =>
  api.post<SeatSelectionContext>(`/public/transport/signatures/${token}/seats`, payload);

export const listVehicleLayouts = () => api.get<VehicleLayoutListResponse>("/transport/layouts");

export const createVehicleLayoutRequest = (payload: VehicleLayoutPayload) =>
  api.post<VehicleLayoutDetail>("/transport/layouts", payload);

export const getVehicleLayoutDetail = (layoutId: number) =>
  api.get<VehicleLayoutDetail>(`/transport/layouts/${layoutId}`);

export const updateVehicleLayoutRequest = (layoutId: number, payload: VehicleLayoutPayload) =>
  api.put<VehicleLayoutDetail>(`/transport/layouts/${layoutId}`, payload);

export const duplicateVehicleLayout = (layoutId: number) =>
  api.post<VehicleLayoutDetail>(`/transport/layouts/${layoutId}/duplicate`);

export const deleteVehicleLayoutRequest = (layoutId: number) =>
  api.delete(`/transport/layouts/${layoutId}`);

export const listVehiclesRequest = () => api.get<VehicleListResponse>("/transport/vehicles");

export const createVehicleRequest = (payload: VehiclePayload) =>
  api.post<VehicleOut>("/transport/vehicles", payload);

export const updateVehicleRequest = (vehicleId: number, payload: VehiclePayload) =>
  api.put<VehicleOut>(`/transport/vehicles/${vehicleId}`, payload);

export const deleteVehicleRequest = (vehicleId: number) =>
  api.delete(`/transport/vehicles/${vehicleId}`);

export const getTripTransportConfig = (publicId: string) =>
  api.get<TripTransportConfigOut>(`/transport/products/${publicId}/transport-config`);

export const saveTripTransportConfig = (publicId: string, payload: TripTransportConfigPayload) =>
  api.put<TripTransportConfigOut>(`/transport/products/${publicId}/transport-config`, payload);

export const getSeatMapContext = (publicId: string, tripVehicleId?: number) =>
  api.get<SeatMapContext>(`/transport/products/${publicId}/seat-map`, {
    params: tripVehicleId ? { trip_vehicle_id: tripVehicleId } : undefined,
  });

export const assignSeatAdmin = (publicId: string, payload: SeatAdminAssignmentPayload, tripVehicleId?: number) =>
  api.post<SeatMapContext>(`/transport/products/${publicId}/seats/assignments`, payload, {
    params: tripVehicleId ? { trip_vehicle_id: tripVehicleId } : undefined,
  });

export const removePassengerSeat = (publicId: string, passengerId: number) =>
  api.delete(`/transport/products/${publicId}/seats/passengers/${passengerId}`);

export const blockSeatRequest = (publicId: string, payload: SeatBlockPayload, tripVehicleId?: number) =>
  api.post<SeatMapContext>(`/transport/products/${publicId}/seats/block`, payload, {
    params: tripVehicleId ? { trip_vehicle_id: tripVehicleId } : undefined,
  });

export const getSeatHistory = (publicId: string, limit = 20) =>
  api.get<SeatHistoryResponse>(`/transport/products/${publicId}/seat-history`, { params: { limit } });
