import { NotificationListResponseInterface } from "@features/notifications/interfaces/notification-list-response.interface";
import { Observable } from "rxjs";

export interface NotificationServiceInterface {
  refresh(number): void;

  getAll(number): Observable<NotificationListResponseInterface>;

  getUnreadCount(): Observable<number>;

  markAsRead(NotificationInterface): Observable<void>;

  markAsUnread(NotificationInterface): Observable<void>;

  markAllAsRead(): Observable<void>;
}
