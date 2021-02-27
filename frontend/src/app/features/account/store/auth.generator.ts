import { AuthState, initialAuthState } from "@features/account/store/auth.reducers";
import { UserProfileGenerator } from "@shared/generators/user-profile.generator";
import { UserSubscriptionGenerator } from "@shared/generators/user-subscription.generator";
import { UserGenerator } from "@shared/generators/user.generator";

export class AuthGenerator {
  static default(): AuthState {
    return {
      initialized: true,
      user: UserGenerator.user(),
      userProfile: UserProfileGenerator.userProfile(),
      userSubscriptions: [UserSubscriptionGenerator.userSubscription()]
    };
  }

  static anonymous(): AuthState {
    return initialAuthState;
  }
}
