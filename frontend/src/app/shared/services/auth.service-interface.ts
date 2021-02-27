import { Observable } from "rxjs";

export interface AuthServiceInterface {
  login(handle: string, password: string, redirectUrl?: string): Observable<string>;

  logout(): void;

  isAuthenticated(): Observable<boolean>;
}
