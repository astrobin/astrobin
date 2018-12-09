import { Injectable } from '@angular/core';
import { UserProfileModel } from "../models/common/userprofile.model";
import { AppContextService } from "./app-context.service";

@Injectable({
  providedIn: 'root'
})
export class UsersService {
  constructor(private appContext: AppContextService) {
  }

  hasValidRawDataSubscription(user: UserProfileModel) {
    const subscriptions = this.appContext.get().subscriptions;

    if (!subscriptions) {
      return false;
    }

    if(!user.userSubscriptionObjects) {
      return false;
    }

    const ids = subscriptions.filter(s => s.category === "rawdata").map(s => s.id);

    return user.userSubscriptionObjects.filter(us => {
      return ids.indexOf(us.subscription) > -1 && us.valid;
    }).length > 0;
  }
}
