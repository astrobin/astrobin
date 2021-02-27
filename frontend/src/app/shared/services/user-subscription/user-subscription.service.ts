import { Injectable } from "@angular/core";
import { State } from "@app/store/state";
import { Store } from "@ngrx/store";
import { SubscriptionInterface } from "@shared/interfaces/subscription.interface";
import { UserProfileInterface } from "@shared/interfaces/user-profile.interface";
import { UserSubscriptionInterface } from "@shared/interfaces/user-subscription.interface";
import { JsonApiService } from "@shared/services/api/classic/json/json-api.service";
import { BaseService } from "@shared/services/base.service";
import { LoadingService } from "@shared/services/loading.service";
import { UserSubscriptionServiceInterface } from "@shared/services/user-subscription/user-subscription.service-interface";
import { SubscriptionName } from "@shared/types/subscription-name.type";
import { Observable, zip } from "rxjs";
import { map, switchMap, take } from "rxjs/operators";

@Injectable({
  providedIn: "root"
})
export class UserSubscriptionService extends BaseService implements UserSubscriptionServiceInterface {
  constructor(
    public readonly store: Store<State>,
    public loadingService: LoadingService,
    public jsonApiService: JsonApiService
  ) {
    super(loadingService);
  }

  hasValidSubscription(user: UserProfileInterface, subscriptionNames: SubscriptionName[]): Observable<boolean> {
    return this.store.pipe(
      take(1),
      map(state => {
        for (const subscriptionName of subscriptionNames) {
          const subscription: SubscriptionInterface = state.app.subscriptions.filter(
            s => s.name === subscriptionName
          )[0];

          if (
            state.auth.userSubscriptions.filter(userSubscription => {
              const expiration = new Date(userSubscription.expires);
              expiration.setUTCHours(23, 59, 59, 999);
              return userSubscription.subscription === subscription.id && expiration >= new Date();
            }).length > 0
          ) {
            return true;
          }
        }

        return false;
      })
    );
  }

  uploadAllowed(): Observable<boolean> {
    return this.store.pipe(
      take(1),
      switchMap(state =>
        zip(
          this.hasValidSubscription(state.auth.userProfile, [
            SubscriptionName.ASTROBIN_ULTIMATE_2020,
            SubscriptionName.ASTROBIN_PREMIUM,
            SubscriptionName.ASTROBIN_PREMIUM_AUTORENEW,
            SubscriptionName.ASTROBIN_PREMIUM_2020
          ]),
          this.hasValidSubscription(state.auth.userProfile, [SubscriptionName.ASTROBIN_LITE_2020]),
          this.hasValidSubscription(state.auth.userProfile, [
            SubscriptionName.ASTROBIN_LITE,
            SubscriptionName.ASTROBIN_LITE_AUTORENEW
          ])
        ).pipe(
          map(([isUltimateOrPremium, isLite2020, isLite]) => ({
            premiumCounter: state.auth.userProfile.premiumCounter,
            backendConfig: state.app.backendConfig,
            isUltimateOrPremium,
            isLite2020,
            isLite
          }))
        )
      ),
      map(({ premiumCounter, backendConfig, isUltimateOrPremium, isLite2020, isLite }) => {
        if (isUltimateOrPremium) {
          return true;
        }

        if (isLite2020) {
          return premiumCounter < backendConfig.PREMIUM_MAX_IMAGES_LITE_2020;
        }

        if (isLite) {
          return premiumCounter < backendConfig.PREMIUM_MAX_IMAGES_LITE;
        }

        // If we got here, the user is on Free.
        return premiumCounter < backendConfig.PREMIUM_MAX_IMAGES_FREE_2020;
      })
    );
  }

  fileSizeAllowed(size: number): Observable<{ allowed: boolean; max: number }> {
    return this.store.pipe(
      take(1),
      switchMap(state =>
        zip(
          this.hasValidSubscription(state.auth.userProfile, [
            SubscriptionName.ASTROBIN_ULTIMATE_2020,
            SubscriptionName.ASTROBIN_PREMIUM,
            SubscriptionName.ASTROBIN_PREMIUM_AUTORENEW,
            SubscriptionName.ASTROBIN_LITE,
            SubscriptionName.ASTROBIN_LITE_AUTORENEW
          ]),
          this.hasValidSubscription(state.auth.userProfile, [SubscriptionName.ASTROBIN_PREMIUM_2020]),
          this.hasValidSubscription(state.auth.userProfile, [SubscriptionName.ASTROBIN_LITE_2020])
        ).pipe(
          map(([isUltimateOrEquivalent, isPremium, isLite]) => ({
            backendConfig: state.app.backendConfig,
            isUltimateOrEquivalent,
            isPremium,
            isLite
          }))
        )
      ),
      map(({ backendConfig, isUltimateOrEquivalent, isPremium, isLite }) => {
        if (isUltimateOrEquivalent) {
          return { allowed: true, max: Number.MAX_SAFE_INTEGER };
        }

        if (isPremium) {
          return {
            allowed: size < backendConfig.PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020,
            max: backendConfig.PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020
          };
        }

        if (isLite) {
          return {
            allowed: size < backendConfig.PREMIUM_MAX_IMAGE_SIZE_LITE_2020,
            max: backendConfig.PREMIUM_MAX_IMAGE_SIZE_LITE_2020
          };
        }

        // If we got here, the user is on Free.
        return {
          allowed: size < backendConfig.PREMIUM_MAX_IMAGE_SIZE_FREE_2020,
          max: backendConfig.PREMIUM_MAX_IMAGE_SIZE_FREE_2020
        };
      })
    );
  }

  getSubscription(userSubscription: UserSubscriptionInterface): Observable<SubscriptionInterface | null> {
    return this.store.pipe(
      take(1),
      map(state => {
        let ret: SubscriptionInterface = null;

        state.app.subscriptions.forEach(subscription => {
          if (subscription.id === userSubscription.subscription) {
            ret = subscription;
          }
        });

        return ret;
      })
    );
  }
}
