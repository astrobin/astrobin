import { GroupModel } from "./group.model";

export class SubscriptionModel {
  id: number;
  name: string;
  description: string;
  price: string;
  trial_period: number;
  trial_unit: string;
  recurrence_period: number;
  recurrence_unit: string;
  category: string;
  group: GroupModel;

  constructor(values: Object = {}) {
    Object.assign(this, values);
  }
}
