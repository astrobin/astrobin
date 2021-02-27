import { BackendConfigInterface } from "@shared/interfaces/backend-config.interface";
import { Observable } from "rxjs";

export interface JsonApiServiceInterface {
  getBackendConfig(): Observable<BackendConfigInterface>;
}
