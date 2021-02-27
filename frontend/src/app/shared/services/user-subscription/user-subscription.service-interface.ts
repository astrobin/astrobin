import { Observable } from "rxjs";
import { UserProfileInterface } from "../../interfaces/user-profile.interface";
import { SubscriptionName } from "../../types/subscription-name.type";

export interface UserSubscriptionServiceInterface {
  // Return true if the user has _any_ of the subscriptions in `subscriptionNames`.
  hasValidSubscription(user: UserProfileInterface, subscriptionNames: SubscriptionName[]): Observable<boolean>;
}
