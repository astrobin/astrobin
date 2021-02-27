import { Component, OnInit } from "@angular/core";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { PayableProductInterface } from "@features/subscriptions/interfaces/payable-product.interface";
import { PricingInterface } from "@features/subscriptions/interfaces/pricing.interface";
import { SubscriptionsService } from "@features/subscriptions/services/subscriptions.service";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { TitleService } from "@shared/services/title/title.service";
import { Observable } from "rxjs";
import { takeUntil } from "rxjs/operators";

@Component({
  selector: "astrobin-subscriptions-options-page",
  templateUrl: "./subscriptions-options-page.component.html",
  styleUrls: ["./subscriptions-options-page.component.scss"]
})
export class SubscriptionsOptionsPageComponent extends BaseComponentDirective implements OnInit {
  litePricing$: Observable<PricingInterface>;
  premiumPricing$: Observable<PricingInterface>;
  ultimatePricing$: Observable<PricingInterface>;

  constructor(
    public readonly store$: Store<State>,
    public readonly classicRoutesService: ClassicRoutesService,
    public readonly subscriptionsService: SubscriptionsService,
    public readonly translate: TranslateService,
    public readonly titleService: TitleService
  ) {
    super();
  }

  ngOnInit(): void {
    const title = this.translate.instant("Subscription plans");
    this.store$.dispatch(new SetBreadcrumb({ breadcrumb: [{ label: "Subscriptions" }, { label: title }] }));

    this.subscriptionsService.currency$.pipe(takeUntil(this.destroyed$)).subscribe(() => {
      this.litePricing$ = this.subscriptionsService.getPrice(PayableProductInterface.LITE);
      this.premiumPricing$ = this.subscriptionsService.getPrice(PayableProductInterface.PREMIUM);
      this.ultimatePricing$ = this.subscriptionsService.getPrice(PayableProductInterface.ULTIMATE);
    });
  }
}
