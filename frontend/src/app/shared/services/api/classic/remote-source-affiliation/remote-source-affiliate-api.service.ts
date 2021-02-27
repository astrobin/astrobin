import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { RemoteSourceAffiliateInterface } from "@shared/interfaces/remote-source-affiliate.interface";
import { BaseClassicApiService } from "@shared/services/api/classic/base-classic-api.service";
import { PaginatedApiResultInterface } from "@shared/services/api/interfaces/paginated-api-result.interface";
import { LoadingService } from "@shared/services/loading.service";
import { EMPTY, Observable } from "rxjs";
import { expand, reduce } from "rxjs/operators";

@Injectable({
  providedIn: "root"
})
export class RemoteSourceAffiliateApiService extends BaseClassicApiService {
  configUrl = this.baseUrl + "/remote-source-affiliation/remote-source-affiliate/";

  constructor(public readonly loadingService: LoadingService, public readonly http: HttpClient) {
    super(loadingService);
  }

  getAll(): Observable<RemoteSourceAffiliateInterface[]> {
    return this.http.get<PaginatedApiResultInterface<RemoteSourceAffiliateInterface>>(this.configUrl).pipe(
      expand(response => (response.next ? this.http.get(response.next) : EMPTY)),
      reduce(
        (accumulator, response) =>
          accumulator.concat((response as PaginatedApiResultInterface<RemoteSourceAffiliateInterface>).results),
        []
      )
    );
  }
}
