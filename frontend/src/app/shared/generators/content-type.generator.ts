import { ContentTypeInterface } from "@shared/interfaces/content-type.interface";

export class ContentTypeGenerator {
  static contentType(): ContentTypeInterface {
    return {
      id: 1,
      appLabel: "astrobin",
      model: "foo"
    };
  }
}
