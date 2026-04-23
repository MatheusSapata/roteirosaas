import api from "./api";
import type {
  SaleSeatSelectionProductsResponse,
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

export const getPostSaleSeatStatus = (token: string) =>
  api.get<SeatPostSignatureStatus>(`/public/transport/sales/${token}/status`);

export const getSaleSeatSelectionProducts = (token: string) =>
  api.get<SaleSeatSelectionProductsResponse>(`/public/transport/sales/${token}/products`);

export const getPublicSeatSelectionContext = (token: string, tripVehicleId?: number, departureId?: number) =>
  api.get<SeatSelectionContext>(`/public/transport/signatures/${token}/seats`, {
    params: {
      ...(tripVehicleId ? { trip_vehicle_id: tripVehicleId } : {}),
      ...(departureId ? { departure_id: departureId } : {}),
    },
  });

export const getPublicSaleSeatSelectionContext = (
  token: string,
  tripVehicleId?: number,
  departureId?: number,
  productPublicId?: string | null,
) =>
  api.get<SeatSelectionContext>(`/public/transport/sales/${token}/seats`, {
    params: {
      ...(tripVehicleId ? { trip_vehicle_id: tripVehicleId } : {}),
      ...(departureId ? { departure_id: departureId } : {}),
      ...(productPublicId ? { product_public_id: productPublicId } : {}),
    },
  });

export const selectSeatForSignature = (token: string, payload: SeatAssignmentPayload, departureId?: number) =>
  api.post<SeatSelectionContext>(`/public/transport/signatures/${token}/seats`, payload, {
    params: departureId ? { departure_id: departureId } : undefined,
  });

export const selectSeatForSale = (
  token: string,
  payload: SeatAssignmentPayload,
  departureId?: number,
  productPublicId?: string | null,
) =>
  api.post<SeatSelectionContext>(`/public/transport/sales/${token}/seats`, payload, {
    params: {
      ...(departureId ? { departure_id: departureId } : {}),
      ...(productPublicId ? { product_public_id: productPublicId } : {}),
    },
  });

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

export const getSeatMapContext = (publicId: string, tripVehicleId?: number, departureId?: number) =>
  api.get<SeatMapContext>(`/transport/products/${publicId}/seat-map`, {
    params: {
      ...(tripVehicleId ? { trip_vehicle_id: tripVehicleId } : {}),
      ...(departureId ? { departure_id: departureId } : {}),
    },
  });

export const assignSeatAdmin = (
  publicId: string,
  payload: SeatAdminAssignmentPayload,
  tripVehicleId?: number,
  departureId?: number,
) =>
  api.post<SeatMapContext>(`/transport/products/${publicId}/seats/assignments`, payload, {
    params: {
      ...(tripVehicleId ? { trip_vehicle_id: tripVehicleId } : {}),
      ...(departureId ? { departure_id: departureId } : {}),
    },
  });

export const removePassengerSeat = (publicId: string, passengerId: number) =>
  api.delete(`/transport/products/${publicId}/seats/passengers/${passengerId}`);

export const blockSeatRequest = (
  publicId: string,
  payload: SeatBlockPayload,
  tripVehicleId?: number,
  departureId?: number,
) =>
  api.post<SeatMapContext>(`/transport/products/${publicId}/seats/block`, payload, {
    params: {
      ...(tripVehicleId ? { trip_vehicle_id: tripVehicleId } : {}),
      ...(departureId ? { departure_id: departureId } : {}),
    },
  });

export const getSeatHistory = (publicId: string, limit = 20, departureId?: number) =>
  api.get<SeatHistoryResponse>(`/transport/products/${publicId}/seat-history`, {
    params: {
      limit,
      ...(departureId ? { departure_id: departureId } : {}),
    },
  });
