import { GroupInterface } from "@shared/interfaces/group.interface";

export interface PaymentInterface {
  id: number;
  timestamp: string;
  event: string;
  amount: string;
  currency: string;
}
