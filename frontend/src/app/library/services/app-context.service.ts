import { Injectable } from '@angular/core';
import { forkJoin } from "rxjs";
import { flatMap, share } from "rxjs/operators";
import { SubscriptionModel } from "../models/common/subscription.model";
import { UserProfileModel } from "../models/common/userprofile.model";
import { CommonApiService } from "./api/common-api.service";

export interface IAppContext {
  currentUserProfile: UserProfileModel,
  subscriptions: SubscriptionModel[]
}

@Injectable({
  providedIn: 'root'
})
export class AppContextService {
  private _appContext = {} as IAppContext;
  private _getCurrentUserProfile$ = this.commonApi.getCurrentUserProfile().pipe(share());
  private _getCurrentUser$ = this._getCurrentUserProfile$.pipe(
    flatMap(userProfile => this.commonApi.getUser(userProfile.user)),
    share());
  private _getUserSubscriptions$ = this._getCurrentUser$.pipe(
    flatMap(user => this.commonApi.getUserSubscriptions(user)),
    share());
  private _getSubscriptions$ = this.commonApi.getSubscriptions().pipe(share())

  constructor(public commonApi: CommonApiService) {
  }

  load(): Promise<any> {
    return forkJoin(
      this._getCurrentUserProfile$,
      this._getCurrentUser$,
      this._getUserSubscriptions$,
      this._getSubscriptions$
    ).toPromise().then((results) => {
      const userProfile: UserProfileModel = {
        ...results[0],
        ...{userObject: results[1]},
        ...{userSubscriptionObjects: results[2]}
      };

      this._appContext = {
        currentUserProfile: userProfile,
        subscriptions: results[3],
      };
    });
  }

  get(): IAppContext {
    return this._appContext;
  }
}
