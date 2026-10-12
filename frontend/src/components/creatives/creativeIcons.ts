import type { Component } from "vue";
import {
  BedDoubleIcon,
  BusIcon,
  CameraIcon,
  CheckIcon,
  CoffeeIcon,
  LuggageIcon,
  MapPinIcon,
  PlaneIcon,
  ShieldCheckIcon,
  ShipIcon,
  TicketIcon,
  UserRoundIcon,
  UtensilsIcon,
  WavesIcon
} from "lucide-vue-next";

const plain = (value: string) => value.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

const RULES: Array<[RegExp, Component]> = [
  [/aere|voo|passage|aviao/, PlaneIcon],
  [/bagage|mala/, LuggageIcon],
  [/cafe/, CoffeeIcon],
  [/hotel|hosped|pousada|resort|quarto|acomoda|diaria/, BedDoubleIcon],
  [/pensao|refei|almoc|jantar|bebida|all inclusive|gastron/, UtensilsIcon],
  [/translad|traslad|transfer|onibus|transporte|4x4|veiculo/, BusIcon],
  [/passeio|city tour|tour|excurs|ingresso|parque/, CameraIcon],
  [/seguro|assistencia|seguranca/, ShieldCheckIcon],
  [/guia|acompanha|monitor/, UserRoundIcon],
  [/cruzeiro|navio|cabine|barco/, ShipIcon],
  [/praia|mergulho|piscina|cachoeira|flutua/, WavesIcon],
  [/taxa|ingresso/, TicketIcon],
  [/roteiro|destino|cidade/, MapPinIcon]
];

/** Ícone do item incluso, pelo texto ("Passagem aérea" → avião, "Café da manhã" → xícara). */
export const inclusionIcon = (label: string): Component => RULES.find(([pattern]) => pattern.test(plain(label)))?.[1] || CheckIcon;
