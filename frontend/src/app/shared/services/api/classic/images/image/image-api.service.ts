import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { State } from "@app/store/state";
import { environment } from "@env/environment";
import { Store } from "@ngrx/store";
import { ImageAlias } from "@shared/enums/image-alias.enum";
import { ImageThumbnailInterface } from "@shared/interfaces/image-thumbnail.interface";
import { ImageInterface } from "@shared/interfaces/image.interface";
import { BaseClassicApiService } from "@shared/services/api/classic/base-classic-api.service";
import { PaginatedApiResultInterface } from "@shared/services/api/interfaces/paginated-api-result.interface";
import { LoadingService } from "@shared/services/loading.service";
import { Observable, throwError } from "rxjs";
import { map } from "rxjs/operators";

@Injectable({
  providedIn: "root"
})
export class ImageApiService extends BaseClassicApiService {
  configUrl = this.baseUrl + "/images";

  constructor(
    public readonly loadingService: LoadingService,
    public readonly store$: Store<State>,
    public readonly http: HttpClient
  ) {
    super(loadingService);
  }

  getImage(id: number | string): Observable<ImageInterface> {
    if (isNaN(Number(id))) {
      const url = `${this.configUrl}/image/?hashes=${id}`;
      return this.http.get<PaginatedApiResultInterface<ImageInterface>>(url).pipe(
        map(response => {
          if (response.results.length > 0) {
            return response.results[0];
          }
          throwError({ statusCode: 404 });
        })
      );
    }

    return this.http.get<ImageInterface>(`${this.configUrl}/image/${id}/`);
  }

  getImages(ids: number[]): Observable<PaginatedApiResultInterface<ImageInterface>> {
    return this.http.get<PaginatedApiResultInterface<ImageInterface>>(`${this.configUrl}/image/?ids=${ids.join(",")}`);
  }

  getImagesByUserId(userId: number): Observable<PaginatedApiResultInterface<ImageInterface>> {
    return this.http.get<PaginatedApiResultInterface<ImageInterface>>(`${this.configUrl}/image/?user=${userId}`);
  }

  getThumbnail(id: number | string, revision: string, alias: ImageAlias): Observable<ImageThumbnailInterface> {
    return this.http.get<ImageThumbnailInterface>(`${environment.classicBaseUrl}/${id}/${revision}/thumb/${alias}/`);
  }

  updateImage(image: ImageInterface): Observable<ImageInterface> {
    return this.http.put<ImageInterface>(`${this.configUrl}/image/${image.pk}/`, image);
  }
}
