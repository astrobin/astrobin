export interface NotificationInterface {
  id: number;
  user: number;
  fromUser?: number;
  subject: string;
  message: string;
  level: number;
  extraTags: string;
  created: string;
  modified: string;
  read: boolean;
  expires?: string;
  closeTimeout?: number;
}
