import { CurrencyPipe } from "@angular/common";
import { Component, OnInit } from "@angular/core";
import { DomSanitizer, SafeHtml } from "@angular/platform-browser";
import { ActivatedRoute, Router } from "@angular/router";
import { SetBreadcrumb } from "@app/store/actions/breadcrumb.actions";
import { State } from "@app/store/state";
import { selectCurrentUser, selectCurrentUserProfile } from "@features/account/store/auth.selectors";
import { PayableProductInterface } from "@features/subscriptions/interfaces/payable-product.interface";
import { PaymentsApiConfigInterface } from "@features/subscriptions/interfaces/payments-api-config.interface";
import { PricingInterface } from "@features/subscriptions/interfaces/pricing.interface";
import { PaymentsApiService } from "@features/subscriptions/services/payments-api.service";
import { SubscriptionsService } from "@features/subscriptions/services/subscriptions.service";
import { Store } from "@ngrx/store";
import { TranslateService } from "@ngx-translate/core";
import { BaseComponentDirective } from "@shared/components/base-component.directive";
import { ImageApiService } from "@shared/services/api/classic/images/image/image-api.service";
import { JsonApiService } from "@shared/services/api/classic/json/json-api.service";
import { ClassicRoutesService } from "@shared/services/classic-routes.service";
import { LoadingService } from "@shared/services/loading.service";
import { PopNotificationsService } from "@shared/services/pop-notifications.service";
import { TitleService } from "@shared/services/title/title.service";
import { UserSubscriptionService } from "@shared/services/user-subscription/user-subscription.service";
import { Observable } from "rxjs";
import { distinctUntilChanged, map, startWith, switchMap, take, takeUntil, tap } from "rxjs/operators";

declare var Stripe: any;

@Component({
  selector: "astrobin-subscriptions-buy-page",
  templateUrl: "./subscriptions-buy-page.component.html",
  styleUrls: ["./subscriptions-buy-page.component.scss"]
})
export class SubscriptionsBuyPageComponent extends BaseComponentDirective implements OnInit {
  PayableProductInterface = PayableProductInterface;

  alreadySubscribed$: Observable<boolean>;
  alreadySubscribedHigher$: Observable<boolean>;
  numberOfImages$: Observable<number>;
  pricing$: Observable<PricingInterface>;
  product: PayableProductInterface;
  bankDetailsMessage$: Observable<string>;
  bankLocations = [
    { id: "USA", label: "United States of America" },
    { id: "CA", label: "Canada" },
    { id: "EU", label: "Europe" },
    { id: "GB", label: "Great Britain" },
    { id: "AUS", label: "Australia" },
    { id: "CH", label: "Switzerland" },
    { id: "CN", label: "China" }
  ];
  selectedBankLocation = "USA";
  currencyPipe: CurrencyPipe;

  constructor(
    public readonly store$: Store<State>,
    public readonly activatedRoute: ActivatedRoute,
    public readonly router: Router,
    public readonly userSubscriptionService: UserSubscriptionService,
    public readonly paymentsApiService: PaymentsApiService,
    public readonly loadingService: LoadingService,
    public readonly popNotificationsService: PopNotificationsService,
    public readonly translate: TranslateService,
    public readonly titleService: TitleService,
    public readonly subscriptionsService: SubscriptionsService,
    public readonly classicRoutesService: ClassicRoutesService,
    public readonly jsonApiService: JsonApiService,
    public readonly imageApiService: ImageApiService,
    public readonly domSanitizer: DomSanitizer
  ) {
    super();

    this.translate.onLangChange
      .pipe(takeUntil(this.destroyed$), startWith({ lang: this.translate.currentLang }))
      .subscribe(event => {
        this.currencyPipe = new CurrencyPipe(event.lang);
      });
  }

  get moreInfoMessage() {
    const url = "https://welcome.astrobin.com/pricing";

    return this.translate.instant(
      "For more information about this and other subscription plans, please visit the {{0}}pricing{{1}} page.",
      {
        0: `<a href="${url}" target="_blank">`,
        1: `</a>`
      }
    );
  }

  get upgradeMessage(): string {
    return this.translate.instant(
      "AstroBin doesn't support subscription upgrades at the moment, but we're happy to make it happen manually. If " +
        "you're on a lower subscription tier and would like to upgrade to <strong>{{0}}</strong>, please just buy it " +
        "and then contact us at {{1}} to get a refund for the unused time on your old subscription. Thanks!",
      {
        0: this.subscriptionsService.getName(this.product),
        1: "<a href=\"mailto:support@astrobin.com\">support@astrobin.com</a>"
      }
    );
  }

  get bankDetails(): string {
    switch (this.selectedBankLocation) {
      case "CH":
        return (
          "BANK       : PostFinance Switzerland\n" +
          "BENEFICIARY: Salvatore Iovene\n" +
          "IBAN       : CH97 0900 0000 6922 3618 4\n" +
          "SWIFT / BIC: POFICHBEXXX"
        );
      case "AU":
        return "BENEFICIARY: AstroBin\n" + "ACCOUNT #  : 412756021\n" + "BSB CODE   : 802-985";
      case "GB":
        return (
          "BENEFICIARY: AstroBin\n" +
          "ACCOUNT #  : 52990073\n" +
          "SORT CODE  : 23-14-70\n" +
          "IBAN       : GB79 TRWI 2314 7052 9900 73"
        );
      case "CA":
        return (
          "BENEFICIARY       : AstroBin\n" +
          "ACCOUNT NUMBER    : 200110016315\n" +
          "INSTITUTION NUMBER: 621\n" +
          "TRANSIT NUMBER    : 16001"
        );
      case "EU":
        return "BENEFICIARY: AstroBin\n" + "IBAN       : BE76 9671 5599 8695\n" + "SWIFT / BIC: TRWIBEB1XXX ";
      case "USA":
        return (
          "Paying from inside the USA\n" +
          "ACCOUNT #: 9600000000061714\n" +
          "ROUTING #: 084009519\n\n" +
          "Paying from outside the USA\n" +
          "ACCOUNT #: 8310788830\n" +
          "SWIFT/BIC: CMFGUS33"
        );
      default:
        return this.translate.instant(
          "Sorry, unfortunately AstroBin does not have a bank account in the selected territory."
        );
    }
  }

  ngOnInit(): void {
    this.loadingService.setLoading(true);

    this.activatedRoute.params.pipe(takeUntil(this.destroyed$)).subscribe(params => {
      this.product = params["product"];

      if (
        [PayableProductInterface.LITE, PayableProductInterface.PREMIUM, PayableProductInterface.ULTIMATE].indexOf(
          this.product
        ) === -1
      ) {
        this.router.navigateByUrl("/page-not-found", { skipLocationChange: true });
        return;
      }

      const title = this.subscriptionsService.getName(this.product);
      this.titleService.setTitle(title);
      this.store$.dispatch(
        new SetBreadcrumb({
          breadcrumb: [{ label: "Subscriptions" }, { label: title }]
        })
      );

      this.alreadySubscribed$ = this.store$
        .select(selectCurrentUserProfile)
        .pipe(
          switchMap(userProfile =>
            this.userSubscriptionService.hasValidSubscription(
              userProfile,
              this.subscriptionsService.getSameTier(this.product)
            )
          )
        );

      this.alreadySubscribedHigher$ = this.store$
        .select(selectCurrentUserProfile)
        .pipe(
          switchMap(userProfile =>
            this.userSubscriptionService.hasValidSubscription(
              userProfile,
              this.subscriptionsService.getHigherTier(this.product)
            )
          )
        );

      this.numberOfImages$ = this.store$
        .select(selectCurrentUser)
        .pipe(switchMap(user => this.imageApiService.getImagesByUserId(user.id).pipe(map(response => response.count))));

      this.subscriptionsService.currency$
        .pipe(takeUntil(this.destroyed$), distinctUntilChanged())
        .subscribe(currency => {
          this.selectedBankLocation = {
            USD: "USA",
            CAD: "CA",
            EUR: "EU",
            GBP: "GB",
            AUD: "AUS",
            CHF: "CH",
            CNY: "CN"
          }[currency];

          this.pricing$ = this.subscriptionsService.getPrice(this.product).pipe(
            takeUntil(this.destroyed$),
            tap(() => this.loadingService.setLoading(false))
          );

          this.bankDetailsMessage$ = this.pricing$.pipe(
            takeUntil(this.destroyed$),
            map(pricing => pricing.price),
            switchMap(price =>
              this.translate.stream(
                "Please make a deposit of {{ currency }} {{ amount }} to the following bank details and then email " +
                  "us at {{ email_prefix }}{{ email }}{{ email_postfix }} with your username so we may upgrade your " +
                  "account manually.",
                {
                  currency: "",
                  amount: `<strong>${this.currencyPipe.transform(price, this.subscriptionsService.currency)}</strong>`,
                  email_prefix: "<a href='mailto:support@astrobin.com'>",
                  email: "support@astrobin.com",
                  email_postfix: "</a>"
                }
              )
            )
          );
        });
    });
  }

  getLiteLimitMessage(numberOfImages): SafeHtml {
    return this.domSanitizer.bypassSecurityTrustHtml(
      this.translate.instant(
        "The Lite plan is capped at <strong>{{maxImagesForLite}}</strong> total images, and you currently have " +
          "<strong>{{numberOfImages}}</strong> images on AstroBin. For this reason, we recommend that you upgrade to " +
          "Premium or Ultimate instead.",
        {
          maxImagesForLite: 50,
          numberOfImages
        }
      )
    );
  }

  buy(): void {
    let stripe: any;
    let config: PaymentsApiConfigInterface;
    let userId: number;

    this.loadingService.setLoading(true);

    this.store$
      .pipe(
        tap(state => {
          userId = state.auth.user.id;
        }),
        switchMap(() => this.paymentsApiService.getConfig().pipe(tap(_config => (config = _config)))),
        switchMap(() => {
          stripe = Stripe(config.publicKey);
          return this.paymentsApiService.createCheckoutSession(
            userId,
            this.product,
            this.subscriptionsService.currency
          );
        })
      )
      .subscribe(response => {
        if (response.sessionId) {
          stripe.redirectToCheckout({ sessionId: response.sessionId });
        } else {
          this.popNotificationsService.error(response.error || this.translate.instant("Unknown error"));
          this.loadingService.setLoading(false);
        }
      });
  }
}
