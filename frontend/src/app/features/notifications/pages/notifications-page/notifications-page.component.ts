import { Component, OnInit } from "@angular/core";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { NotificationInterface } from "@features/notifications/interfaces/notification.interface";
import { NotificationsService } from "@features/notifications/services/notifications.service";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { TitleService } from "@shared/services/title/title.service";
import { take } from "rxjs/operators";

@Component({
  selector: "astrobin-notifications-page",
  templateUrl: "./notifications-page.component.html",
  styleUrls: ["./notifications-page.component.scss"]
})
export class NotificationsPageComponent extends BaseComponentDirective implements OnInit {
  page = 1;
  pageTitle = this.translate.instant("Notifications");

  constructor(
    public store$: Store<State>,
    public notificationsService: NotificationsService,
    public classicRoutesService: ClassicRoutesService,
    public titleService: TitleService,
    public translate: TranslateService
  ) {
    super();

    titleService.setTitle(this.pageTitle);
    this.store$.dispatch(
      new SetBreadcrumb({
        breadcrumb: [{ label: this.pageTitle }]
      })
    );
  }

  ngOnInit(): void {
    this.notificationsService.refresh();
  }

  toggleRead(notification: NotificationInterface): void {
    const method = notification.read ? this.notificationsService.markAsUnread : this.notificationsService.markAsRead;

    method
      .call(this.notificationsService, notification)
      .pipe(take(1))
      .subscribe();
  }

  markAllAsRead(): void {
    this.notificationsService
      .markAllAsRead()
      .pipe(take(1))
      .subscribe();
  }

  pageChange(page: number): void {
    this.page = page;
    this.notificationsService
      .getAll(page)
      .pipe(take(1))
      .subscribe();
  }
}
