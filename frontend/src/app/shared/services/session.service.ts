import { Injectable } from "@angular/core";
import { BaseService } from "@shared/services/base.service";

@Injectable({
  providedIn: "root"
})
export class SessionService extends BaseService {
  private readonly _storage: any = {};

  public get(key: string): any {
    return this._storage[key];
  }

  public put(key: string, data: any): void {
    this._storage[key] = data;
  }

  public delete(key: string): void {
    delete this._storage[key];
  }
}
