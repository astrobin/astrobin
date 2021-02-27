import { Pipe, PipeTransform } from "@angular/core";
import { UserProfileInterface } from "@shared/interfaces/user-profile.interface";
import { Observable } from "rxjs";
import { UserStoreService } from "../services/user-store.service";
import { UserSubscriptionService } from "../services/user-subscription/user-subscription.service";
import { SubscriptionName } from "../types/subscription-name.type";

@Pipe({
  name: "hasValidUserSubscription"
})
export class HasValidUserSubscriptionPipe implements PipeTransform {
  constructor(public userStoreService: UserStoreService, public userSubscriptionService: UserSubscriptionService) {}

  transform(userProfile: UserProfileInterface, subscriptionNames: SubscriptionName[]): Observable<boolean> {
    return this.userSubscriptionService.hasValidSubscription(userProfile, subscriptionNames);
  }
}
