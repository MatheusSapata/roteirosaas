import type { PageLeadCaptureConfig } from "./leads";

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
  | "free_footer_brand";

export interface SectionBase {
  type: SectionType;
  enabled: boolean;
  backgroundColor?: string;
  textColor?: string;
  fullWidth?: boolean;
  anchorId?: string;
  headingLabel?: string;
  headingLabelStyle?: "filled" | "outline";
}

export interface HeroSection extends SectionBase {
  type: "hero";
  title: string;
  subtitle?: string;
  backgroundImage?: string;
  gradientColor?: string;
  logoUrl?: string;
  logoSize?: number;
  logoBorderRadius?: number;
  chips?: string[];
  ctaLabel?: string;
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
  title: string;
  subtitle?: string;
  backgroundImage?: string;
  gradientColor?: string;
  cardBackground?: string;
  cardBorderColor?: string;
  textColor?: string;
  bodyColor?: string;
  ctaLabel?: string;
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
  altText?: string;
}

export interface BiographySection extends SectionBase {
  type: "biography";
  title: string;
  text: string;
  image?: string;
  mobileImage?: string;
  overlayOpacity?: number;
  titleColor?: string;
}

export type CurrencyCode = "BRL" | "USD" | "EUR" | "ARS";

export interface PriceItem {
  title: string;
  price: number;
  description?: string;
  currency?: CurrencyCode;
  titleLabel?: string;
  priceLabel?: string;
  badge?: string;
  highlight?: boolean;
  ctaLabel?: string;
  ctaLink?: string;
}

export interface PricesSection extends SectionBase {
  type: "prices";
  items: PriceItem[];
  layout?: "cards" | "columns" | "highlight";
  ctaColor?: string;
  description?: string;
  ctaLabel?: string;
  ctaLink?: string;
  title?: string;
  subtitle?: string;
}

export interface ItineraryDay {
  id?: string;
  day: string;
  title: string;
  description: string;
  image?: string;
}

export interface ItinerarySection extends SectionBase {
  type: "itinerary";
  days: ItineraryDay[];
  layout?: "timeline" | "cards" | "minimal" | "steps";
  ctaColor?: string;
  title?: string;
  subtitle?: string;
}

export interface FaqItem {
  question: string;
  answer: string;
}

export interface FaqSection extends SectionBase {
  type: "faq";
  items: FaqItem[];
  layout?: "accordion" | "split" | "compact";
  title?: string;
  subtitle?: string;
}

export interface Testimonial {
  name: string;
  text: string;
  avatar?: string;
  role?: string;
}

export interface TestimonialsSection extends SectionBase {
  type: "testimonials";
  items: Testimonial[];
  layout?: "grid" | "stacked" | "highlight" | "cards";
  title?: string;
  subtitle?: string;
  ctaLabel?: string;
  ctaLink?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  ctaColor?: string;
  cardColor?: string;
}

export interface FeaturedVideoSection extends SectionBase {
  type: "featured_video";
  title: string;
  subtitle?: string;
  videoUrl?: string;
  ctaEnabled?: boolean;
  ctaLabel?: string;
  ctaLink?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  ctaColor?: string;
}

export interface CountdownSection extends SectionBase {
  type: "countdown";
  targetDate: string;
  label?: string;
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

export interface FreeFooterBrandSection extends SectionBase {
  type: "free_footer_brand";
  text: string;
  align?: "left" | "center" | "right";
}

export interface StorySection extends SectionBase {
  type: "story";
  layout?: "single" | "gallery";
  imagePosition?: "left" | "right";
  badge?: string;
  title: string;
  subtitle?: string;
  ctaLabel?: string;
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
  title: string;
  description?: string;
}

export interface ReasonsSection extends SectionBase {
  type: "reasons";
  title: string;
  subtitle?: string;
  items: ReasonItem[];
  backgroundColor?: string;
  layout?: "grid";
  enableAnimation?: boolean;
  animationDuration?: number;
  cardAnimationStagger?: number;
}

export interface CtaSection extends SectionBase {
  type: "cta";
  label: string;
  link?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  description?: string;
  layout?: "bar" | "split" | "card" | "simple";
  ctaColor?: string;
  backgroundImage?: string;
  textColor?: string;
  ctaText?: string;
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

