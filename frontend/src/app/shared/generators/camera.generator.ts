import { CameraInterface } from "@shared/interfaces/camera.interface";

export class CameraGenerator {
  static camera(): CameraInterface {
    return {
      pk: 1,
      make: "Some brand",
      name: "Some model"
    };
  }
}
