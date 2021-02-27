import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { GroupInterface } from "@shared/interfaces/group.interface";
import { BaseClassicApiService } from "@shared/services/api/classic/base-classic-api.service";
import { PaginatedApiResultInterface } from "@shared/services/api/interfaces/paginated-api-result.interface";
import { LoadingService } from "@shared/services/loading.service";
import { EMPTY, Observable } from "rxjs";
import { expand, reduce } from "rxjs/operators";

@Injectable({
  providedIn: "root"
})
export class GroupApiService extends BaseClassicApiService {
  configUrl = this.baseUrl + "/groups/group/";

  constructor(public readonly loadingService: LoadingService, public readonly http: HttpClient) {
    super(loadingService);
  }

  getAll(memberId?: number): Observable<GroupInterface[]> {
    let url = this.configUrl;

    if (memberId !== undefined) {
      url += "?member=" + memberId;
    }

    return this.http.get<PaginatedApiResultInterface<GroupInterface>>(url).pipe(
      expand(response => (response.next ? this.http.get(response.next) : EMPTY)),
      reduce(
        (accumulator, response) =>
          accumulator.concat((response as PaginatedApiResultInterface<GroupInterface>).results),
        []
      )
    );
  }
}
