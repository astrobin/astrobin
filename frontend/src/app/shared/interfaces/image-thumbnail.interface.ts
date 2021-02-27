import { ImageAlias } from "@shared/enums/image-alias.enum";

export interface ImageThumbnailInterface {
  id: number;
  revision: string;
  alias: ImageAlias;
  url: string;
}
