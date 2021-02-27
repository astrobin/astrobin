export interface ThumbnailAliases {
  [key: string]: {
    size: number[];
    [property: string]: any;
  };
}

export interface BackendConfigInterface {
  version?: string;
  i18nHash: string;
  readOnly: boolean;
  PREMIUM_MAX_IMAGES_FREE: number;
  PREMIUM_MAX_IMAGES_LITE: number;
  PREMIUM_MAX_IMAGES_FREE_2020: number;
  PREMIUM_MAX_IMAGES_LITE_2020: number;
  PREMIUM_MAX_IMAGES_PREMIUM_2020: number;
  PREMIUM_MAX_IMAGE_SIZE_FREE_2020: number;
  PREMIUM_MAX_IMAGE_SIZE_LITE_2020: number;
  PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020: number;
  PREMIUM_MAX_REVISIONS_FREE_2020: number;
  PREMIUM_MAX_REVISIONS_LITE_2020: number;
  PREMIUM_MAX_REVISIONS_PREMIUM_2020: number;
  PREMIUM_PRICE_FREE_2020: number;
  PREMIUM_PRICE_LITE_2020: number;
  PREMIUM_PRICE_PREMIUM_2020: number;
  PREMIUM_PRICE_ULTIMATE_2020: number;
  MAX_IMAGE_PIXELS: number;
  GOOGLE_ADS_ID?: string;
  REQUEST_COUNTRY: string;
  IMAGE_CONTENT_TYPE_ID: number;
  THUMBNAIL_ALIASES: ThumbnailAliases;
  IOTD_SUBMISSION_MAX_PER_DAY: number;
  IOTD_REVIEW_MAX_PER_DAY: number;
  IOTD_QUEUES_PAGE_SIZE: number;
}
