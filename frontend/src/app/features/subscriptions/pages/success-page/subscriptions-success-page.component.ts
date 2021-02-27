import { Component, OnInit } from "@angular/core";
import { ActivatedRoute } from "@angular/router";
import { AppState } from "@app/store/reducers/app.reducers";
import { selectApp } from "@app/store/selectors/app/app.selectors";
import { State } from "@app/store/state";
import { SubscriptionsService } from "@features/subscriptions/services/subscriptions.service";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { TitleService } from "@shared/services/title/title.service";

declare const gtag: any;

@Component({
  selector: "astrobin-subscriptions-success-page",
  templateUrl: "./subscriptions-success-page.component.html",
  styleUrls: ["./subscriptions-success-page.component.scss"]
})
export class SubscriptionsSuccessPageComponent implements OnInit {
  constructor(
    public readonly store: Store<State>,
    public readonly titleService: TitleService,
    public readonly translate: TranslateService,
    public readonly activatedRoute: ActivatedRoute,
    public readonly subscriptionsService: SubscriptionsService
  ) {}

  ngOnInit(): void {
    this.titleService.setTitle(this.translate.instant("Subscription confirmed"));

    const product = this.activatedRoute.snapshot.queryParams["product"];

    if (!!product) {
      this.store.select(selectApp).subscribe(state => {
        const googleAdsId = state.backendConfig.GOOGLE_ADS_ID;
        const conversionId = this.subscriptionsService.getConversionId(product);

        if (googleAdsId) {
          gtag("event", "conversion", {
            send_to: `${googleAdsId}/${conversionId}`
          });
        }
      });
    }
  }
}
