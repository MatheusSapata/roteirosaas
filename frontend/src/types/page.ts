export type SectionType =
  | "hero"
  | "gallery"
  | "prices"
  | "itinerary"
  | "faq"
  | "testimonials"
  | "cta"
  | "story"
  | "reasons"
  | "countdown"
  | "free_footer_brand";

export interface SectionBase {
  type: SectionType;
  enabled: boolean;
  backgroundColor?: string;
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
  chips?: string[];
  ctaLabel?: string;
  ctaLink?: string;
  ctaMode?: "link" | "section";
  ctaSectionId?: string | null;
  ctaColor?: string;
  videoUrl?: string;
  layout?: "classic" | "split" | "card" | "immersive";
}

export interface GallerySection extends SectionBase {
  type: "gallery";
  images: string[];
  layout?: "mosaic" | "grid" | "strip";
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
}

export interface PricesSection extends SectionBase {
  type: "prices";
  items: PriceItem[];
  layout?: "cards" | "columns" | "highlight";
  ctaColor?: string;
  description?: string;
}

export interface ItineraryDay {
  day: string;
  title: string;
  description: string;
}

export interface ItinerarySection extends SectionBase {
  type: "itinerary";
  days: ItineraryDay[];
  layout?: "timeline" | "cards" | "minimal" | "steps";
}

export interface FaqItem {
  question: string;
  answer: string;
}

export interface FaqSection extends SectionBase {
  type: "faq";
  items: FaqItem[];
  layout?: "accordion" | "split" | "compact";
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

export interface CountdownSection extends SectionBase {
  type: "countdown";
  targetDate: string;
  label?: string;
  backgroundColor?: string;
  textColor?: string;
  layout?: "bar" | "flip";
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
  images: string[];
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
}

export type PageSection =
  | HeroSection
  | GallerySection
  | PricesSection
  | ItinerarySection
  | FaqSection
  | TestimonialsSection
  | CtaSection
  | StorySection
  | ReasonsSection
  | CountdownSection
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
}
