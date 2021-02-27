import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { CameraInterface } from "@shared/interfaces/camera.interface";
import { BaseClassicApiService } from "@shared/services/api/classic/base-classic-api.service";
import { CameraApiServiceInterface } from "@shared/services/api/classic/gear/camera/camera-api.service-interface";
import { LoadingService } from "@shared/services/loading.service";
import { Observable } from "rxjs";

@Injectable({
  providedIn: "root"
})
export class CameraApiService extends BaseClassicApiService implements CameraApiServiceInterface {
  configUrl = this.baseUrl + "/astrobin/camera";

  constructor(public readonly loadingService: LoadingService, public readonly http: HttpClient) {
    super(loadingService);
  }

  getCamera(id: number): Observable<CameraInterface> {
    return this.http.get<CameraInterface>(`${this.configUrl}/${id}/`);
  }
}
