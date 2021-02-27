import { ThumbnailGroupInterface } from "@shared/interfaces/thumbnail-group.interface";
import { Observable } from "rxjs";

export interface ThumbnailGroupApiServiceInterface {
  getThumbnailGroup(imageId: number, revision: string): Observable<ThumbnailGroupInterface>;
}
