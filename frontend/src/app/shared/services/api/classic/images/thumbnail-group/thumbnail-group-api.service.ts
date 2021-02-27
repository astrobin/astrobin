import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { ListResponseInterface } from "@shared/interfaces/list-response.interface";
import { ThumbnailGroupInterface } from "@shared/interfaces/thumbnail-group.interface";
import { BaseClassicApiService } from "@shared/services/api/classic/base-classic-api.service";
import { LoadingService } from "@shared/services/loading.service";
import { Observable } from "rxjs";
import { map } from "rxjs/operators";
import { ThumbnailGroupApiServiceInterface } from "./thumbnail-group-api.service-interface";

@Injectable({
  providedIn: "root"
})
export class ThumbnailGroupApiService extends BaseClassicApiService implements ThumbnailGroupApiServiceInterface {
  configUrl = this.baseUrl + "/images/thumbnail-group";

  constructor(public loadingService: LoadingService, private http: HttpClient) {
    super(loadingService);
  }

  getThumbnailGroup(imageId: number, revision: string): Observable<ThumbnailGroupInterface> {
    return this.http.get<ListResponseInterface<ThumbnailGroupInterface>>(`${this.configUrl}/?image=${imageId}`).pipe(
      map(response => {
        const results = response.results.filter(result => result.revision === revision);

        if (results) {
          return results[0];
        }

        return null;
      })
    );
  }
}
