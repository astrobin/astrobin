import { Component, OnInit } from "@angular/core";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { TitleService } from "@shared/services/title/title.service";

@Component({
  selector: "astrobin-subscriptions-cancelled-page",
  templateUrl: "./subscriptions-cancelled-page.component.html",
  styleUrls: ["./subscriptions-cancelled-page.component.scss"]
})
export class SubscriptionsCancelledPageComponent implements OnInit {
  constructor(
    public store$: Store<State>,
    public readonly titleService: TitleService,
    public readonly translate: TranslateService
  ) {}

  ngOnInit(): void {
    const title = this.translate.instant("Subscription process cancelled");
    this.titleService.setTitle(title);
    this.store$.dispatch(new SetBreadcrumb({ breadcrumb: [{ label: "Subscriptions" }, { label: title }] }));
  }
}
