import api from "./api";
import type {
  AutoMatchApplyPayload,
  AutoMatchApplyResponse,
  AutoMatchPreviewResponse,
  CreateRoomPayload,
  MovePassengerPayload,
  ReplacePassengerPayload,
  RoomingListResponse,
  RoomingRoom,
  SwapPassengersPayload,
} from "../types/rooming";

export const getRoomingList = (productId: string) =>
  api.get<RoomingListResponse>(`/finance/products/${productId}/rooming-list`);

export const createRoom = (productId: string, payload: CreateRoomPayload) =>
  api.post<RoomingRoom>(`/finance/products/${productId}/rooming-list/rooms`, payload);

export const removePassengerFromRoom = (productId: string, roomId: number, passengerId: number) =>
  api.delete<RoomingRoom>(
    `/finance/products/${productId}/rooming-list/rooms/${roomId}/assignments/${passengerId}`,
  );

export const renameRoom = (productId: string, roomId: number, name: string) =>
  api.patch<RoomingRoom>(`/finance/products/${productId}/rooming-list/rooms/${roomId}`, { name });

export const previewAutoMatch = (productId: string) =>
  api.post<AutoMatchPreviewResponse>(`/finance/products/${productId}/rooming-list/auto-match/preview`, {});

export const applyAutoMatch = (productId: string, payload: AutoMatchApplyPayload) =>
  api.post<AutoMatchApplyResponse>(`/finance/products/${productId}/rooming-list/auto-match/apply`, payload);

export const movePassenger = (productId: string, payload: MovePassengerPayload) =>
  api.post<RoomingRoom>(`/finance/products/${productId}/rooming-list/move-passenger`, payload);

export const swapPassengers = (productId: string, payload: SwapPassengersPayload) =>
  api.post<void>(`/finance/products/${productId}/rooming-list/swap-passengers`, payload);

export const replacePassenger = (productId: string, payload: ReplacePassengerPayload) =>
  api.post<void>(`/finance/products/${productId}/rooming-list/replace-passenger`, payload);
