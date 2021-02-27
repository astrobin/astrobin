import { ImageInterface } from "../interfaces/image.interface";

export class ImageGenerator {
  static image(source: Partial<ImageInterface> = {}): ImageInterface {
    return {
      user: source.user || 1,
      pk: source.pk || 1,
      hash: source.hash || "abc123",
      title: source.title || "Generated image",
      imageFile: source.imageFile || "/media/images/generated.jpg",
      isWip: source.isWip || false,
      skipNotifications: source.skipNotifications || false,
      w: source.w || 1000,
      h: source.h || 1000,
      imagingTelescopes: source.imagingTelescopes || [],
      imagingCameras: source.imagingCameras || [],
      published: source.published || new Date().toISOString()
    };
  }
}
