import { ImageAlias } from "@shared/enums/image-alias.enum";
import { BackendConfigInterface } from "@shared/interfaces/backend-config.interface";

export class BackendConfigGenerator {
  static backendConfig(): BackendConfigInterface {
    return {
      i18nHash: "bc587c72ede144236ed01f2f5f8b290e",
      readOnly: false,
      PREMIUM_MAX_IMAGES_FREE: 10,
      PREMIUM_MAX_IMAGES_LITE: 12,
      PREMIUM_MAX_IMAGES_FREE_2020: 10,
      PREMIUM_MAX_IMAGES_LITE_2020: 50,
      PREMIUM_MAX_IMAGES_PREMIUM_2020: 999999,
      PREMIUM_MAX_IMAGE_SIZE_FREE_2020: 1024 * 1024 * 25,
      PREMIUM_MAX_IMAGE_SIZE_LITE_2020: 1024 * 1024 * 25,
      PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020: 1024 * 1024 * 50,
      PREMIUM_MAX_REVISIONS_FREE_2020: 0,
      PREMIUM_MAX_REVISIONS_LITE_2020: 1,
      PREMIUM_MAX_REVISIONS_PREMIUM_2020: 5,
      PREMIUM_PRICE_FREE_2020: 0,
      PREMIUM_PRICE_LITE_2020: 20,
      PREMIUM_PRICE_PREMIUM_2020: 40,
      PREMIUM_PRICE_ULTIMATE_2020: 60,
      MAX_IMAGE_PIXELS: 16536 * 16536,
      GOOGLE_ADS_ID: "GOOGLE_ADS_1234",
      REQUEST_COUNTRY: "us",
      IMAGE_CONTENT_TYPE_ID: 1,
      THUMBNAIL_ALIASES: {
        [ImageAlias.REGULAR]: {
          size: [620, 0]
        },
        [ImageAlias.GALLERY]: {
          size: [130, 130]
        }
      },
      IOTD_SUBMISSION_MAX_PER_DAY: 3,
      IOTD_REVIEW_MAX_PER_DAY: 3,
      IOTD_QUEUES_PAGE_SIZE: 10
    };
  }
}
