import { Injectable } from "@angular/core";
import { Observable } from "rxjs";

@Injectable()
export abstract class AuthApiService {
  abstract login(handle: string, password: string): Observable<string>;
}
