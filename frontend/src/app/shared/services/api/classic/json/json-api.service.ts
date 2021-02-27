import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { environment } from "@env/environment";
import { BackendConfigInterface } from "@shared/interfaces/backend-config.interface";
import { JsonApiServiceInterface } from "@shared/services/api/classic/json/json-api.service-interface";
import { LoadingService } from "@shared/services/loading.service";
import { Observable } from "rxjs";
import { BaseClassicApiService } from "../base-classic-api.service";

@Injectable({
  providedIn: "root"
})
export class JsonApiService extends BaseClassicApiService implements JsonApiServiceInterface {
  configUrl = environment.classicApiUrl + "/json-api";

  constructor(public loadingService: LoadingService, private http: HttpClient) {
    super(loadingService);
  }

  getBackendConfig(): Observable<BackendConfigInterface> {
    return this.http.get<BackendConfigInterface>(`${this.configUrl}/common/app-config/`);
  }
}
