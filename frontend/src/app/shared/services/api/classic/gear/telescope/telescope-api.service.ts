import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { TelescopeInterface } from "@shared/interfaces/telescope.interface";
import { BaseClassicApiService } from "@shared/services/api/classic/base-classic-api.service";
import { TelescopeApiServiceInterface } from "@shared/services/api/classic/gear/telescope/telescope-api.service-interface";
import { LoadingService } from "@shared/services/loading.service";
import { Observable } from "rxjs";

@Injectable({
  providedIn: "root"
})
export class TelescopeApiService extends BaseClassicApiService implements TelescopeApiServiceInterface {
  configUrl = this.baseUrl + "/astrobin/telescope";

  constructor(public readonly loadingService: LoadingService, public readonly http: HttpClient) {
    super(loadingService);
  }

  getTelescope(id: number): Observable<TelescopeInterface> {
    return this.http.get<TelescopeInterface>(`${this.configUrl}/${id}/`);
  }
}
