import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { NotificationListResponseInterface } from "@features/notifications/interfaces/notification-list-response.interface";
import { NotificationInterface } from "@features/notifications/interfaces/notification.interface";
import { BaseClassicApiService } from "@shared/services/api/classic/base-classic-api.service";
import { LoadingService } from "@shared/services/loading.service";
import { Observable } from "rxjs";

@Injectable({
  providedIn: "root"
})
export class NotificationsApiService extends BaseClassicApiService {
  configUrl = this.baseUrl + "/notifications/notification";

  constructor(public loadingService: LoadingService, public http: HttpClient) {
    super(loadingService);
  }

  getAll(page = 1): Observable<NotificationListResponseInterface> {
    return this.http.get<NotificationListResponseInterface>(`${this.configUrl}/?page=${page}`);
  }

  getUnreadCount(): Observable<number> {
    return this.http.get<number>(`${this.configUrl}/get_unread_count/`);
  }

  update(notification: NotificationInterface): Observable<void> {
    if (!notification.extraTags) {
      notification.extraTags = "-";
    }

    return this.http.put<void>(`${this.configUrl}/${notification.id}/`, notification);
  }

  markAllAsRead(): Observable<void> {
    return this.http.post<void>(`${this.configUrl}/mark_all_as_read/`, null);
  }
}
