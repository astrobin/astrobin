import { TelescopeInterface } from "@shared/interfaces/telescope.interface";
import { Observable } from "rxjs";

export interface TelescopeApiServiceInterface {
  getTelescope(id: number): Observable<TelescopeInterface>;
}
