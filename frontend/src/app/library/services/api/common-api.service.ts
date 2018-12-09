import { HttpClient } from "@angular/common/http";
import { Injectable } from '@angular/core';
import { Observable } from "rxjs";
import { map } from "rxjs/operators";
import { SubscriptionModel } from "../../models/common/subscription.model";
import { UserProfileModel } from "../../models/common/userprofile.model";
import { UserModel } from "../../models/common/user.model";
import { UserSubscriptionModel } from "../../models/common/usersubscription.model";
import { BaseApiService } from "./base-api.service";

@Injectable({
  providedIn: 'root'
})
export class CommonApiService extends BaseApiService {
  configUrl = this.baseUrl + '/common';

  constructor(private http: HttpClient) {
    super();
  }

  getUser(id: number): Observable<UserModel> {
    return this.http.get<UserModel>(this.configUrl + "/users/" + id).pipe(
      map(response => new UserModel(response))
    );
  }

  getCurrentUserProfile(): Observable<UserProfileModel> {
    return this.http.get<UserProfileModel[]>(this.configUrl + '/userprofiles/current').pipe(
      map(response => {
        if(response.length > 0) {
          return new UserProfileModel(response[0]);
        }

        return null;
      })
    )
  }

  isAuthenticated(): Observable<boolean> {
    return new Observable(observer => {
      this.getCurrentUserProfile().subscribe(userProfile => {
        observer.next(userProfile !== null);
        observer.complete();
      });
    });
  }

  getSubscriptions(): Observable<SubscriptionModel[]> {
    return this.http.get<SubscriptionModel[]>(`${this.configUrl}/subscriptions`);
  }

  getUserSubscriptions(user?: UserModel): Observable<UserSubscriptionModel[]> {
    let url = `${this.configUrl}/usersubscriptions/`;
    if (user) {
      url += `?user=${user.id}`;
    }

    return this.http.get<UserSubscriptionModel[]>(url);
  }
}
