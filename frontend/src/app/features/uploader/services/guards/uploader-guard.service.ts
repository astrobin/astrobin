import { Injectable } from "@angular/core";
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from "@angular/router";
import { BaseService } from "@shared/services/base.service";
import { PremiumSubscriptionGuardService } from "@shared/services/guards/premium-subscription-guard.service";
import { UltimateSubscriptionGuardService } from "@shared/services/guards/ultimate-subscription-guard.service";
import { LoadingService } from "@shared/services/loading.service";
import { concat, Observable } from "rxjs";
import { reduce, tap } from "rxjs/operators";

@Injectable()
export class UploaderGuardService extends BaseService implements CanActivate {
  constructor(
    public loadingService: LoadingService,
    public premiumGuard: PremiumSubscriptionGuardService,
    public ultimateGuard: UltimateSubscriptionGuardService,
    public router: Router
  ) {
    super(loadingService);
  }

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean> {
    return concat(
      this.premiumGuard.canActivate(route, state, false),
      this.ultimateGuard.canActivate(route, state, false)
    ).pipe(
      reduce((acc, val) => acc || val),
      tap(result => {
        if (!result) {
          this.router.navigateByUrl(this.router.createUrlTree(["/permission-denied"]));
          return false;
        }
      })
    );
  }
}
