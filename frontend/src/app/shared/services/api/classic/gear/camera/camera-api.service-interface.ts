import { CameraInterface } from "@shared/interfaces/camera.interface";
import { Observable } from "rxjs";

export interface CameraApiServiceInterface {
  getCamera(id: number): Observable<CameraInterface>;
}
