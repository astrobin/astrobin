export class UserSubscriptionModel {
  id: number;
  valid: boolean;
  expires: string;
  active: boolean;
  cancelled: boolean;
  user: number;
  subscription: number;

  constructor(values: Object = {}) {
    Object.assign(this, values);
  }
}
