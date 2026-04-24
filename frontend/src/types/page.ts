import type { PageLeadCaptureConfig } from "./leads";
import type { LocalizedString } from "../utils/i18n";

export type SectionType =
  | "hero"
  | "banner_card"
  | "gallery"
  | "photo"
  | "biography"
  | "prices"
  | "itinerary"
  | "faq"
  | "testimonials"
  | "featured_video"
  | "cta"
  | "story"
  | "reasons"
  | "countdown"
  | "agency_footer"
  | "flight_details"
  | "free_footer_brand";

export interface SectionBase {
  type: SectionType;
  enabled: boolean;
  backgroundColor?: string;
  textColor?: string;
  fullWidth?: boolean;
  anchorId?: string;
  headingLabel?: LocalizedString;
  headingLabelStyle?: "filled" | "outline";
}

export interface HeroSection extends SectionBase {
  type: "hero";
  title: LocalizedString;
  subtitle?: LocalizedString;
  backgroundImage?: string;
  gradientColor?: string;
  logoUrl?: string;
  logoSize?: number;
  logoBorderRadius?: number;
  chips?: LocalizedString[];
  ctaLabel?: LocalizedString;
  ctaLink?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  ctaColor?: string;
  videoUrl?: string;
  layout?: "classic" | "split" | "card" | "immersive";
  enableAnimation?: boolean;
  animationDuration?: number;
  ctaShimmer?: boolean;
}

export interface BannerCardSection extends SectionBase {
  type: "banner_card";
  title: LocalizedString;
  subtitle?: LocalizedString;
  backgroundImage?: string;
  gradientColor?: string;
  cardBackground?: string;
  cardBorderColor?: string;
  textColor?: string;
  bodyColor?: string;
  ctaLabel?: LocalizedString;
  ctaLink?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  ctaColor?: string;
}

export interface GallerySection extends SectionBase {
  type: "gallery";
  images: string[];
  layout?: "mosaic" | "grid" | "strip";
}

export interface PhotoSection extends SectionBase {
  type: "photo";
  image?: string;
  layout?: "card" | "full";
  altText?: LocalizedString;
}

export interface BiographySection extends SectionBase {
  type: "biography";
  title: LocalizedString;
  text: LocalizedString;
  image?: string;
  mobileImage?: string;
  overlayOpacity?: number;
  titleColor?: string;
  titleFontSize?: number;
  textFontSize?: number;
}

export type CurrencyCode = "BRL" | "USD" | "EUR" | "ARS";

export interface PriceItem {
  title: LocalizedString;
  price: number;
  description?: LocalizedString;
  currency?: CurrencyCode;
  titleLabel?: LocalizedString;
  priceLabel?: LocalizedString;
  badge?: LocalizedString;
  highlight?: boolean;
  ctaLabel?: LocalizedString;
  ctaLink?: string;
}

export interface PricesSection extends SectionBase {
  type: "prices";
  items: PriceItem[];
  layout?: "cards" | "columns" | "highlight";
  ctaColor?: string;
  description?: LocalizedString;
  ctaLabel?: LocalizedString;
  ctaLink?: string;
  title?: LocalizedString;
  subtitle?: LocalizedString;
}

export interface ItineraryDay {
  id?: string;
  day: LocalizedString;
  title: LocalizedString;
  description: LocalizedString;
  image?: string;
}

export interface ItinerarySection extends SectionBase {
  type: "itinerary";
  days: ItineraryDay[];
  layout?: "timeline" | "cards" | "minimal" | "steps";
  ctaColor?: string;
  title?: LocalizedString;
  subtitle?: LocalizedString;
}

export interface FaqItem {
  question: LocalizedString;
  answer: LocalizedString;
}

export interface FaqSection extends SectionBase {
  type: "faq";
  items: FaqItem[];
  layout?: "accordion" | "split" | "compact";
  title?: LocalizedString;
  subtitle?: LocalizedString;
}

export interface Testimonial {
  name: LocalizedString;
  text: LocalizedString;
  avatar?: string;
  role?: LocalizedString;
}

export interface TestimonialsSection extends SectionBase {
  type: "testimonials";
  items: Testimonial[];
  layout?: "grid" | "stacked" | "highlight" | "cards";
  title?: LocalizedString;
  subtitle?: LocalizedString;
  ctaLabel?: LocalizedString;
  ctaLink?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  ctaColor?: string;
  cardColor?: string;
}

export interface FeaturedVideoSection extends SectionBase {
  type: "featured_video";
  title: LocalizedString;
  subtitle?: LocalizedString;
  videoUrl?: string;
  ctaEnabled?: boolean;
  ctaLabel?: LocalizedString;
  ctaLink?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  ctaColor?: string;
}

export interface CountdownSection extends SectionBase {
  type: "countdown";
  targetDate: string;
  label?: LocalizedString;
  backgroundColor?: string;
  textColor?: string;
  layout?: "bar" | "flip";
}

export interface AgencyFooterSection extends SectionBase {
  type: "agency_footer";
  showCadastur?: boolean;
  displayVariant?: "auto" | "stacked" | "wide";
  fullWidth?: boolean;
}

export interface FlightSectionSegment {
  id?: number;
  journey_id?: number;
  sort_order?: number;
  source_mode?: "manual" | "airlabs" | "aerodatabox";
  flight_number?: string;
  flight_iata?: string;
  flight_icao?: string;
  flight_date?: string;
  airline_name?: string;
  airline_iata?: string;
  airline_icao?: string;
  airline_logo_url?: string;
  departure_airport_iata?: string;
  departure_airport_name?: string;
  departure_city?: string;
  departure_country?: string;
  departure_terminal?: string;
  departure_gate?: string;
  departure_datetime?: string;
  arrival_airport_iata?: string;
  arrival_airport_name?: string;
  arrival_city?: string;
  arrival_country?: string;
  arrival_terminal?: string;
  arrival_gate?: string;
  arrival_datetime?: string;
  duration_minutes?: number;
  cabin_class?: string;
  status?: string;
  included_personal_item?: boolean;
  included_carry_on?: boolean;
  included_checked_bag?: boolean;
  notes?: string;
  raw_provider_response?: Record<string, any> | null;
}

export interface FlightSectionJourney {
  id?: number;
  page_id?: number;
  section_id?: string;
  direction: "outbound" | "inbound";
  title?: string;
  sort_order?: number;
  is_enabled?: boolean;
  segments: FlightSectionSegment[];
}

export interface FlightDetailsSection extends SectionBase {
  type: "flight_details";
  sectionId?: string;
  title?: LocalizedString;
  subtitle?: LocalizedString;
  visualStyle?: "compact" | "decolar";
  showOutbound?: boolean;
  showInbound?: boolean;
  journeys?: FlightSectionJourney[];
  lookupAvailable?: boolean;
}

export interface FreeFooterBrandSection extends SectionBase {
  type: "free_footer_brand";
  text: LocalizedString;
  align?: "left" | "center" | "right";
}

export interface StorySection extends SectionBase {
  type: "story";
  layout?: "single" | "gallery";
  imagePosition?: "left" | "right";
  badge?: LocalizedString;
  title: LocalizedString;
  subtitle?: LocalizedString;
  ctaLabel?: LocalizedString;
  ctaLink?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  ctaColor?: string;
  ctaEnabled?: boolean;
  enableAnimation?: boolean;
  ctaShimmer?: boolean;
  images: string[];
  videoUrls?: string[];
  videoUrl?: string;
  backgroundColor?: string;
  borderEnabled?: boolean;
  borderColor?: string;
}

export interface ReasonItem {
  icon?: string;
  title: LocalizedString;
  description?: LocalizedString;
}

export interface ReasonsSection extends SectionBase {
  type: "reasons";
  title: LocalizedString;
  subtitle?: LocalizedString;
  items: ReasonItem[];
  backgroundColor?: string;
  layout?: "grid";
  enableAnimation?: boolean;
  animationDuration?: number;
  cardAnimationStagger?: number;
}

export interface CtaSection extends SectionBase {
  type: "cta";
  label: LocalizedString;
  link?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  description?: LocalizedString;
  layout?: "bar" | "split" | "card" | "simple";
  ctaColor?: string;
  backgroundImage?: string;
  textColor?: string;
  ctaText?: LocalizedString;
  highlight?: boolean;
  highlightColor?: string;
}

export type PageSection =
  | HeroSection
  | BannerCardSection
  | GallerySection
  | PhotoSection
  | BiographySection
  | PricesSection
  | ItinerarySection
  | FaqSection
  | TestimonialsSection
  | FeaturedVideoSection
  | CtaSection
  | StorySection
  | ReasonsSection
  | CountdownSection
  | AgencyFooterSection
  | FlightDetailsSection
  | FreeFooterBrandSection;

export interface ThemeConfig {
  color1: string;
  color2: string;
  heroTheme?: "immersive" | "classic" | "split" | "card";
  ctaDefaultColor?: string;
  ctaTextColor?: string;
  sidebarTheme?: "light" | "dark";
}

export interface EditorPreferences {
  previewEnabled: boolean;
  previewLayout?: "split" | "editor";
  previewDevice?: "desktop" | "mobile";
}

export interface PageConfig {
  sections: PageSection[];
  theme?: ThemeConfig;
  editor?: EditorPreferences;
  version?: number;
  leadCapture?: PageLeadCaptureConfig | null;
  tracking?: any;
}

