import { ImageAlias } from "@shared/enums/image-alias.enum";
import { ImageThumbnailInterface } from "@shared/interfaces/image-thumbnail.interface";

export class ImageThumbnailGenerator {
  static thumbnail(source: Partial<ImageThumbnailInterface> = {}): ImageThumbnailInterface {
    return {
      url: "/media/images/generated.jpg",
      alias: ImageAlias.REGULAR,
      id: 1,
      revision: "original",
      ...source
    };
  }
}
