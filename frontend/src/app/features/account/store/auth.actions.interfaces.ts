import { UserProfileInterface } from "@shared/interfaces/user-profile.interface";
import { UserSubscriptionInterface } from "@shared/interfaces/user-subscription.interface";
import { UserInterface } from "@shared/interfaces/user.interface";

export interface InitializeAuthSuccessInterface {
  user: UserInterface;
  userProfile: UserProfileInterface;
  userSubscriptions: UserSubscriptionInterface[];
}

export interface LoginPayloadInterface {
  handle: string;
  password: string;
  redirectUrl?: string;
}

export interface LoginFailureInterface {
  error: string;
}

export interface LoginSuccessInterface {
  user: UserInterface;
  userProfile: UserProfileInterface;
  userSubscriptions: UserSubscriptionInterface[];
  redirectUrl?: string;
}
