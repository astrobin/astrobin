import { ThumbnailGroupInterface } from "../interfaces/thumbnail-group.interface";

export class ThumbnailGroupGenerator {
  static thumbnailGroup(): ThumbnailGroupInterface {
    return {
      image: 1,
      pk: 1,
      revision: "0",
      real: "/media/thumbnails/1/real.jpg",
      hd: "/media/thumbnails/1/hd.jpg",
      regular: "/media/thumbnails/1/regular.jpg",
      gallery: "/media/thumbnails/1/gallery.jpg",
      thumb: "/media/thumbnails/1/thumb.jpg"
    };
  }
}
