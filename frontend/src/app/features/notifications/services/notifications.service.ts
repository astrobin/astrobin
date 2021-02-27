import { Injectable } from "@angular/core";
import { NotificationListResponseInterface } from "@features/notifications/interfaces/notification-list-response.interface";
import { NotificationInterface } from "@features/notifications/interfaces/notification.interface";
import { NotificationServiceInterface } from "@features/notifications/services/notification.service-interface";
import { NotificationsApiService } from "@features/notifications/services/notifications-api.service";
import { BaseService } from "@shared/services/base.service";
import { LoadingService } from "@shared/services/loading.service";
import { Observable, Subject, throwError } from "rxjs";
import { catchError, switchMap, take, tap } from "rxjs/operators";

@Injectable({
  providedIn: "root"
})
export class NotificationsService extends BaseService implements NotificationServiceInterface {
  notifications$: Observable<NotificationListResponseInterface>;
  unreadCount$: Observable<number>;

  private _notificationsSubject = new Subject<NotificationListResponseInterface>();
  private _unreadCountSubject = new Subject<number>();
  private _lastPage = 1;

  constructor(public loadingService: LoadingService, public api: NotificationsApiService) {
    super(loadingService);
    this.notifications$ = this._notificationsSubject.asObservable();
    this.unreadCount$ = this._unreadCountSubject.asObservable();
  }

  refresh(page = 1): void {
    this.loadingSubject.next(true);

    this.getAll(page)
      .pipe(
        take(1),
        switchMap(() => this.getUnreadCount()),
        catchError(error => {
          this.loadingSubject.next(false);
          return throwError(error.statusText);
        })
      )
      .subscribe(() => this.loadingSubject.next(false));
  }

  getAll(page = 1): Observable<NotificationListResponseInterface> {
    this.loadingSubject.next(true);
    this._lastPage = page;
    return this.api.getAll(page).pipe(
      tap(response => {
        this.loadingSubject.next(false);
        this._notificationsSubject.next(response);
      })
    );
  }

  getUnreadCount(): Observable<number> {
    this.loadingSubject.next(true);
    return this.api.getUnreadCount().pipe(
      tap(() => this.loadingSubject.next(false)),
      tap(response => this._unreadCountSubject.next(response))
    );
  }

  markAsRead(notification: NotificationInterface): Observable<void> {
    this.loadingSubject.next(true);
    notification.read = true;
    return this.api.update(notification).pipe(
      tap(() => this.loadingSubject.next(false)),
      tap(() => this.refresh(this._lastPage))
    );
  }

  markAsUnread(notification: NotificationInterface): Observable<void> {
    this.loadingSubject.next(true);
    notification.read = false;
    return this.api.update(notification).pipe(
      tap(() => this.loadingSubject.next(false)),
      tap(() => this.refresh(this._lastPage))
    );
  }

  markAllAsRead(): Observable<void> {
    this.loadingSubject.next(true);
    return this.api.markAllAsRead().pipe(
      tap(() => this.loadingSubject.next(false)),
      tap(() => this.refresh(this._lastPage))
    );
  }
}
