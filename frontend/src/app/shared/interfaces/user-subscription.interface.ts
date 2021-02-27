export interface UserSubscriptionInterface {
  id: number;
  valid: boolean;
  expires: string;
  active: boolean;
  cancelled: boolean;
  user: number;
  subscription: number;
}
