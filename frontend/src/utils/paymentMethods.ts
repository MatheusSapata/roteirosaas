import americanLogo from "../assets/card-brands/american.png";
import dinersLogo from "../assets/card-brands/diners.png";
import eloLogo from "../assets/card-brands/elo.png";
import hiperLogo from "../assets/card-brands/hiper.png";
import mastercardLogo from "../assets/card-brands/mastercard.svg";
import visaLogo from "../assets/card-brands/visa.png";

/** Formas de pagamento e bandeiras que a seção pode mostrar. */
export type PaymentMethodId = "pix" | "boleto" | "cartao" | "visa" | "mastercard" | "elo" | "amex" | "hipercard" | "diners";

export interface PaymentMethodOption {
  id: PaymentMethodId;
  label: string;
  kind: "method" | "brand";
  logo?: string;
}

export const PAYMENT_METHODS: PaymentMethodOption[] = [
  { id: "pix", label: "Pix", kind: "method" },
  { id: "boleto", label: "Boleto", kind: "method" },
  { id: "cartao", label: "Cartão de crédito", kind: "method" },
  { id: "visa", label: "Visa", kind: "brand", logo: visaLogo },
  { id: "mastercard", label: "Mastercard", kind: "brand", logo: mastercardLogo },
  { id: "elo", label: "Elo", kind: "brand", logo: eloLogo },
  { id: "amex", label: "American Express", kind: "brand", logo: americanLogo },
  { id: "hipercard", label: "Hipercard", kind: "brand", logo: hiperLogo },
  { id: "diners", label: "Diners", kind: "brand", logo: dinersLogo }
];

export const DEFAULT_PAYMENT_METHODS: PaymentMethodId[] = ["pix", "boleto", "cartao", "visa", "mastercard", "elo"];

export const paymentOptionsFor = (ids?: string[] | null) =>
  PAYMENT_METHODS.filter(option => (ids || []).includes(option.id));
