import { Injectable } from "@angular/core";
import { environment } from "@env/environment";
import { Constants } from "@shared/constants";
import { UploadDataServiceInterface } from "@shared/services/upload-metadata/upload-data.service-interface";
import { BehaviorSubject, Observable } from "rxjs";

export interface UploadMetadataInterface {
  [key: string]: any;
}

export interface UploadMetadataEventInterface {
  id: string;
  metadata: UploadMetadataInterface;
}

@Injectable({
  providedIn: "root"
})
export class UploadDataService implements UploadDataServiceInterface {
  metadataChanges$: Observable<UploadMetadataEventInterface>;
  endpointChanges$: Observable<string>;
  allowedTypesChanges$: Observable<string>;

  private _metadata: { [key: string]: UploadMetadataInterface } = {};

  private _metadataChanges = new BehaviorSubject<UploadMetadataEventInterface>(null);

  private _endpointChanges = new BehaviorSubject<string>(`${environment.classicBaseUrl}/api/v2/images/image/`);

  private _allowedTypesChanges = new BehaviorSubject<string>(Constants.ALLOWED_UPLOAD_EXTENSIONS.join());

  constructor() {
    this.metadataChanges$ = this._metadataChanges.asObservable();
    this.endpointChanges$ = this._endpointChanges.asObservable();
    this.allowedTypesChanges$ = this._allowedTypesChanges.asObservable();
  }

  setMetadata(id: string, metadata: UploadMetadataInterface): void {
    this._metadata[id] = metadata;
    this._metadataChanges.next({ id, metadata });
  }

  patchMetadata(id: string, metadata: UploadMetadataInterface): void {
    this._metadata[id] = {
      ...this._metadata[id],
      ...metadata
    };
    this._metadataChanges.next({ id, metadata: this._metadata[id] });
  }

  setEndpoint(endpoint: string) {
    this._endpointChanges.next(endpoint);
  }

  setAllowedTypes(allowedTypes: string) {
    this._allowedTypesChanges.next(allowedTypes);
  }
}
