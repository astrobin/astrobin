import { UserSubscriptionInterface } from "@shared/interfaces/user-subscription.interface";
import { TestConstants } from "@shared/test-constants";

export class UserSubscriptionGenerator {
  static userSubscription(subscription = TestConstants.ASTROBIN_ULTIMATE_2020_ID): UserSubscriptionInterface {
    return {
      id: 1,
      valid: true,
      expires: "2100-12-31",
      active: true,
      cancelled: false,
      user: 1,
      subscription
    };
  }

  static nonExpiredButNotActiveUserSubscription(
    subscription = TestConstants.ASTROBIN_ULTIMATE_2020_ID
  ): UserSubscriptionInterface {
    const userSubscription = this.userSubscription(subscription);
    userSubscription.expires = "3000-01-01";
    userSubscription.active = false;

    return userSubscription;
  }

  static expiredUserSubscription(subscription = TestConstants.ASTROBIN_ULTIMATE_2020_ID): UserSubscriptionInterface {
    const userSubscription = this.userSubscription(subscription);
    userSubscription.expires = "1970-01-01";

    return userSubscription;
  }
}
