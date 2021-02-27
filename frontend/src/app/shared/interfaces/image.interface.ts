export enum AcquisitionType {
  REGULAR = "REGULAR",
  EAA = "EAA",
  LUCKY = "LUCKY",
  DRAWING = "DRAWING",
  OTHER = "OTHER"
}

export enum SubjectType {
  DEEP_SKY = "DEEP_SKY",
  SOLAR_SYSTEM = "SOLAR_SYSTEM",
  WIDE_FIELD = "WIDE_FIELD",
  STAR_TRAILS = "STAR_TRAILS",
  NORTHERN_LIGHTS = "NORTHERN_LIGHTS",
  GEAR = "GEAR",
  OTHER = "OTHER"
}

export enum SolarSystemSubjectType {
  SUN = "SUN",
  MOON = "MOON",
  MERCURY = "MERCURY",
  VENUS = "VENUS",
  MARS = "MARS",
  JUPITER = "JUPITER",
  SATURN = "SATURN",
  URANUS = "URANUS",
  NEPTUNE = "NEPTUNE",
  MINOR_PLANET = "MINOR_PLANET",
  COMET = "COMET",
  OCCULTATION = "OCCULTATION",
  CONJUNCTION = "CONJUNCTION",
  PARTIAL_LUNAR_ECLIPSE = "PARTIAL_LUNAR_ECLIPSE",
  TOTAL_LUNAR_ECLIPSE = "TOTAL_LUNAR_ECLIPSE",
  PARTIAL_SOLAR_ECLIPSE = "PARTIAL_SOLAR_ECLIPSE",
  ANULAR_SOLAR_ECLIPSE = "ANULAR_SOLAR_ECLIPSE",
  TOTAL_SOLAR_ECLIPSE = "TOTAL_SOLAR_ECLIPSE",
  OTHER = "OTHER"
}

export enum DataSource {
  BACKYARD = "BACKYARD",
  TRAVELLER = "TRAVELLER",
  OWN_REMOTE = "OWN_REMOTE",
  AMATEUR_HOSTING = "AMATEUR_HOSTING",
  PUBLIC_AMATEUR_DATA = "PUBLIC_AMATEUR_DATA",
  PRO_DATA = "PRO_DATA",
  MIX = "MIX",
  OTHER = "OTHER",
  UNKNOWN = "UNKNOWN"
}

export enum RemoteSource {
  AC = "AstroCamp",
  AHK = "Astro Hostel Krasnodar",
  AOWA = "Astro Observatories Western Australia",
  CS = "ChileScope",
  DSNM = "Dark Sky New Mexico",
  DSP = "Dark Sky Portal",
  DSC = "DeepSkyChile",
  DSW = "DeepSkyWest",
  eEyE = "e-EyE Extremadura",
  EITS = "Eye In The Sky",
  GFA = "Goldfield Astronomical Observatory",
  GMO = "Grand Mesa Observatory",
  HMO = "Heaven's Mirror Observatory",
  IC = "IC Astronomy Observatories",
  ITU = "Image The Universe",
  INS = "Insight Observatory",
  iT = "iTelescope",
  LGO = "Lijiang Gemini Observatory",
  MARIO = "Marathon Remote Imaging Observatory (MaRIO)",
  NMS = "New Mexico Skies",
  OES = "Observatorio El Sauce",
  PSA = "PixelSkies",
  REM = "RemoteSkies.net",
  REMSG = "Remote Skygems",
  RLD = "Riverland Dingo Observatory",
  ROBO = "RoboScopes",
  SS = "Sahara Sky",
  SPVO = "San Pedro Valley Observatory",
  SRO = "Sierra Remote Observatories",
  SRO2 = "Sky Ranch Observatory",
  SPOO = "SkyPi Remote Observatory",
  SLO = "Slooh",
  SSLLC = "Stellar Skies LLC"
}

export enum MouseHoverImageOptions {
  NOTHING = "NOTHING",
  SOLUTION = "SOLUTION",
  INVERTED = "INVERTED"
}

export interface ImageInterface {
  user: number;
  pk: number;
  hash: string;
  title: string;
  imageFile: string;
  isWip: boolean;
  skipNotifications: boolean;
  w: number;
  h: number;
  imagingTelescopes: number[];
  imagingCameras: number[];
  published: string;
  license: string;
  description?: string;
  link?: string;
  linkToFits?: string;
  acquisitionType: AcquisitionType;
  subjectType: SubjectType;
  solarSystemMainSubject?: SolarSystemSubjectType;
  dataSource: DataSource;
  remoteSource?: string;
  partOfGroupSet: number[];
  keyValueTags?: string;
  mouseHoverImage: MouseHoverImageOptions;
  allowComments: boolean;
}
